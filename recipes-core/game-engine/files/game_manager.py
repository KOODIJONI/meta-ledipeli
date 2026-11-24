from __future__ import annotations

import importlib
import inspect
import queue
import threading

from base_game.base_game import BaseGame
from config import get_fps, get_hand_tracker_socket, get_initial_game, get_matrix_size, get_config_value
from rpc_handlers import GameRpcHandlers
from gpio_buttons import ButtonListener
from hand_client import HandTrackerClient
from mqtt_client import AggregatedMqttClient

SIMULATOR_STATE_TOPIC = "engine/simulator/config"
CAMERA_SIZE_TOPIC = "engine/camera/size"
AVAILABLE_GAMES_TOPIC = "engine/available"


def _get_available_games(config) -> list[str]:
    startup = config.get("startup", {}) if isinstance(config, dict) else {}
    games = startup.get("available_games", ["tetris"])
    return [str(g).strip().lower() for g in games if str(g).strip()]


def build_game(config, game_name=None, mqtt_client=None, tracker=None):
    available_games = _get_available_games(config)
    game_name = (game_name or get_initial_game(config) or "tetris").strip().lower()

    if game_name not in available_games:
        raise ValueError(f"Game '{game_name}' is not enabled. Available games: {available_games}")

    module_path = f"games.{game_name}.{game_name}"
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ValueError(f"Unsupported game '{game_name}': module '{module_path}' not found") from exc

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseGame) and obj is not BaseGame and obj.__module__ == module.__name__:
            return obj(config=config, mqtt_client=mqtt_client, tracker=tracker)

    raise ValueError(f"No BaseGame subclass found in '{module_path}'")


class GameManager:
    def __init__(self, config, mqtt_client=None):
        self.config = config
        self.mqtt_client = mqtt_client if mqtt_client is not None else self._create_common_mqtt_client(config)
        self.buttons = self._setup_buttons()

        socket_path = get_hand_tracker_socket(self.config)
        print(f"[MAIN] Initializing central HandTrackerClient at {socket_path}...")
        self.shared_tracker = HandTrackerClient(socket_path=str(socket_path))

        self.game = None
        self.current_game_name = None
        self.running = False
        self._game_lock = threading.RLock()
        self._game_requests = queue.Queue(maxsize=1)

        if self.mqtt_client is not None:
            self.mqtt_client.add_on_connect(self._publish_all_state)

        self._brightness = get_config_value(config, "engine", "brightness", default=None)

        self.rpc_handlers = GameRpcHandlers(self)
        self.rpc_handlers.register(self.mqtt_client)


    def _create_common_mqtt_client(self, config):
        mqtt_cfg = config.get("mqtt", {}) if isinstance(config, dict) else {}
        broker_url = mqtt_cfg.get("broker_url") or mqtt_cfg.get("broker")
        if not broker_url or not mqtt_cfg.get("enabled", True):
            print("[MAIN] MQTT not configured or disabled.")
            return None

        try:
            return AggregatedMqttClient(broker_url=str(broker_url), client_id="game-manager")
        except Exception as exc:
            print(f"[MAIN] MQTT unavailable: {exc}")
            return None

    # --- Public API for RPC & controls ---

    def get_available_games(self) -> list[str]:
        return _get_available_games(self.config)

    def get_status(self) -> dict:
        simulation = self._get_simulation_settings()
        with self._game_lock:
            game = self.game
            game_name = self.current_game_name

        return {
            "game": game_name,
            "running": bool(self.running and game is not None and getattr(game, "running", False)),
            "simulation": simulation,
        }

    def set_simulation(self, simulation_type: str, enabled: bool) -> dict:
        engine_cfg = self.config.setdefault("engine", {})
        if simulation_type == "matrix":
            engine_cfg["simulate"] = enabled
        elif simulation_type == "input":
            engine_cfg["simulate_input"] = enabled
        else:
            raise ValueError(f"Unknown simulation type: {simulation_type}")

        print(f"[RPC] {simulation_type} simulation requested: {enabled}")
        with self._game_lock:
            game = self.game

        if game is not None:
            if simulation_type == "matrix":
                game.set_simulate_matrix(enabled)
            else:
                game.set_simulate_input(enabled)
            print("[RPC] Actual game simulation settings:", game.get_simulation_settings())
        else:
            print("[RPC] No game instance exists yet.")

        payload = self._publish_simulator_state()
        print("[RPC] Published simulator state:", payload)
        return {"enabled": enabled, "type": simulation_type}

    def cycle_game(self, step: int = 1):
        return self._cycle_game(step)

    def next_game(self):
        return self._cycle_game(+1)

    def previous_game(self):
        return self._cycle_game(-1)

    def request_game_change(self, game_name):
        """Thread-safe. Used by RPC handlers, cycling, and GPIO buttons."""
        game_name = str(game_name).strip().lower()
        if game_name not in _get_available_games(self.config):
            raise ValueError(f"Unsupported or disabled game '{game_name}'")
        if not self.running:
            raise RuntimeError("Application is not running")

        try:
            self._game_requests.put_nowait(game_name)
        except queue.Full:
            raise RuntimeError("A game change is already pending")

        with self._game_lock:
            current_game = self.game
        if current_game is not None:
            current_game.stop()

        return game_name

    # --- State & publishing ---

    def _get_simulation_settings(self):
        engine_cfg = self.config.setdefault("engine", {})
        settings = {
            "simulateMatrix": bool(engine_cfg.get("simulate", False)),
            "simulateInput": bool(engine_cfg.get("simulate_input", False)),
        }

        with self._game_lock:
            game = self.game

        if game is not None:
            try:
                game_settings = game.get_simulation_settings()
                if isinstance(game_settings, dict):
                    settings["simulateMatrix"] = bool(
                        game_settings.get("simulateMatrix", game_settings.get("simulate_matrix", settings["simulateMatrix"]))
                    )
                    settings["simulateInput"] = bool(
                        game_settings.get("simulateInput", game_settings.get("simulate_input", settings["simulateInput"]))
                    )
            except Exception as exc:
                print(f"[MAIN] Could not read game simulation settings: {exc}")

        return settings

    def _publish_simulator_state(self):
        if self.mqtt_client is None:
            return None

        engine_cfg = self.config.setdefault("engine", {})
        matrix_rows, matrix_cols = get_matrix_size(self.config)
        simulation = self._get_simulation_settings()

        payload = {
            "simulateMatrix": simulation["simulateMatrix"],
            "simulateInput": simulation["simulateInput"],
            "matrix": {"width": matrix_cols, "height": matrix_rows},
            "camera": {
                "width": int(engine_cfg.get("width", 640)),
                "height": int(engine_cfg.get("height", 480)),
            },
        }

        self.mqtt_client.publish(SIMULATOR_STATE_TOPIC, payload, retain=True)
        self.mqtt_client.publish(CAMERA_SIZE_TOPIC, payload["camera"], retain=True)
        return payload

    def _publish_available_games(self):
        if self.mqtt_client is None:
            return

        startup = self.config.get("startup", {})
        games = startup.get("available_games", ["tetris"])
        with self._game_lock:
            selected_game = self.current_game_name

        self.mqtt_client.publish(
            AVAILABLE_GAMES_TOPIC,
            {"games": games, "selectedGame": selected_game},
            retain=True,
        )

    def _publish_all_state(self):
        self._publish_available_games()
        self._publish_simulator_state()

    # --- Game lifecycle ---

    def _install_game(self, game_name):
        game_name = str(game_name).strip().lower()
        print(f"[MAIN] Creating game: {game_name}")
        new_game = build_game(self.config, game_name, self.mqtt_client, tracker=self.shared_tracker)

        if self._brightness is not None:
            new_game.set_brightness(float(self._brightness))
            
        with self._game_lock:
            self.game = new_game
            self.current_game_name = game_name

        print(f"[MAIN] Current game: {game_name}")
        self._publish_available_games()
        self._publish_simulator_state()
        return new_game

    def _process_game_request(self):
        try:
            game_name = self._game_requests.get_nowait()
        except queue.Empty:
            return False

        print(f"[MAIN] Processing game change: {game_name}")
        with self._game_lock:
            self.game = None
        self._install_game(game_name)
        print(f"[MAIN] Game transition completed: {game_name}")
        return True

    def _cycle_game(self, step):
        games = _get_available_games(self.config)
        if len(games) < 2:
            return None

        with self._game_lock:
            current = self.current_game_name

        try:
            index = games.index(current)
        except ValueError:
            index = 0

        target = games[(index + step) % len(games)]
        try:
            self.request_game_change(target)
            print(f"[GAME] Switching to game: {target}")
            return target
        except (RuntimeError, ValueError) as exc:
            print(f"[GAME] Ignored game change: {exc}")
            return None

    def run(self, fps=None):
        if self.running:
            raise RuntimeError("Application is already running")

        target_fps = fps or get_fps(self.config)
        initial_game = get_initial_game(self.config) or "tetris"
        self._install_game(initial_game)
        self.running = True

        if self.buttons is not None:
            try:
                self.buttons.start()
                print("[MAIN] GPIO buttons started.")
            except Exception as exc:
                print(f"[MAIN] GPIO buttons unavailable: {exc}")
                self.buttons = None

        print("[MAIN] Application started.")
        try:
            while self.running:
                if self._process_game_request():
                    continue

                with self._game_lock:
                    current_game = self.game
                    current_game_name = self.current_game_name

                if current_game is None:
                    continue

                print(f"[MAIN] Running game: {current_game_name}")
                current_game.run(fps=target_fps)

                if not self.running:
                    break
                if not self._game_requests.empty():
                    continue

                raise RuntimeError(f"Game '{current_game_name}' exited unexpectedly.")
        finally:
            self.stop()

        print("[MAIN] Application stopped.")

    def stop(self):
        if not self.running and self.game is None:
            return

        print("[MAIN] Shutting down application...")
        self.running = False

        with self._game_lock:
            game = self.game

        if game is not None:
            try:
                game.stop()
            except Exception as exc:
                print("[MAIN] Error stopping game:", exc)
                self.running = False

        if getattr(self, "buttons", None) is not None:
            try:
                self.buttons.stop()
            except Exception as exc:
                print(f"[MAIN] Error stopping buttons: {exc}")

        if hasattr(self, "shared_tracker") and self.shared_tracker is not None:
            try:
                self.shared_tracker.stop()
                print("[MAIN] Central HandTrackerClient stopped.")
            except Exception as exc:
                print(f"[MAIN] Error stopping central tracker: {exc}")

        if self.mqtt_client is not None:
            try:
                self.mqtt_client.stop()
            except Exception:
                pass

    def _setup_buttons(self):
        gpio_cfg = self.config.get("gpio", {}) if isinstance(self.config, dict) else {}
        if not gpio_cfg.get("enabled", True):
            return None

        next_pin = int(gpio_cfg.get("next_pin", 4))
        prev_pin = int(gpio_cfg.get("prev_pin", 17))

        buttons = ButtonListener([prev_pin, next_pin], consumer="game-manager")
        buttons.on(next_pin, lambda pin: self.next_game())
        buttons.on(prev_pin, lambda pin: self.previous_game())
        return buttons
    
    def set_matrix_brightness(self, brightness: float) -> float:
        self._brightness = brightness
        with self._game_lock:
            game = self.game
        if game is not None:
            game.set_brightness(brightness)
        if self.mqtt_client is not None:
            self.mqtt_client.publish("engine/matrix/brightness", {"brightness": brightness}, retain=True)
        return brightness

    def toggle_pause(self):
        
        with self._game_lock:
            game = self.game
        if game is not None:
            game.pause()

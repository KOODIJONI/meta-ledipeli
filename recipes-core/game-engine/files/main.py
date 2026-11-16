
from __future__ import annotations

import queue
import threading

from config import (
    get_fps,
    get_initial_game,
    get_matrix_size,
    load_config,
)
from games.test_game.test_game import MatrixGame
from games.tetris.tetris import Tetris
from mqtt_client import AggregatedMqttClient
from parse_arg import parse_args


SIMULATOR_STATE_TOPIC = "engine/simulator/config"
CAMERA_SIZE_TOPIC = "engine/camera/size"
AVAILABLE_GAMES_TOPIC = "engine/available"


GAME_FACTORIES = {
    "tetris": Tetris,
    "test_game": MatrixGame,
    "matrix_game": MatrixGame,
}


# =============================================================
# GAME FACTORY
# =============================================================

def build_game(config, game_name=None, mqtt_client=None):
    startup = config.get("startup", {})
    available_games = startup.get(
        "available_games",
        ["tetris"],
    )

    game_name = (
        game_name or get_initial_game(config) or "tetris"
    ).strip().lower()

    if game_name not in GAME_FACTORIES:
        raise ValueError(
            f"Unsupported game '{game_name}'"
        )

    if (
        game_name not in available_games
        and game_name not in ("test_game", "matrix_game")
    ):
        raise ValueError(
            f"Game '{game_name}' is not enabled. "
            f"Available games: {available_games}"
        )

    factory = GAME_FACTORIES[game_name]

    return factory(
        config=config,
        mqtt_client=mqtt_client,
    )


def select_game(config, mqtt_client=None):
    startup = config.get("startup", {})
    available_games = startup.get(
        "available_games",
        ["tetris"],
    )

    initial_game = get_initial_game(config)

    if (
        initial_game in available_games
        and initial_game in GAME_FACTORIES
    ):
        return build_game(
            config,
            initial_game,
            mqtt_client,
        )

    if (
        "test_game" in available_games
        or "matrix_game" in available_games
    ):
        return build_game(
            config,
            "matrix_game",
            mqtt_client,
        )

    if "tetris" in available_games:
        return build_game(
            config,
            "tetris",
            mqtt_client,
        )

    raise ValueError(
        f"No supported game available in config: "
        f"{available_games}"
    )


# =============================================================
# GAME MANAGER
# =============================================================

class GameManager:

    def __init__(self, config, mqtt_client=None):

        self.config = config

        self.mqtt_client = (
            mqtt_client
            if mqtt_client is not None
            else self._create_common_mqtt_client(config)
        )

        self.game = None
        self.current_game_name = None

        # Application lifecycle
        self.running = False

        # Protect access to the current game reference.
        self._game_lock = threading.RLock()

        # MQTT callbacks submit requests here.
        self._game_requests = queue.Queue(maxsize=1)

        self._setup_jsonrpc()

        if self.mqtt_client is not None:
            self.mqtt_client.add_on_connect(
                self._publish_all_state
            )

    # =========================================================
    # MQTT CLIENT
    # =========================================================

    def _create_common_mqtt_client(self, config):

        mqtt_cfg = (
            config.get("mqtt", {})
            if isinstance(config, dict)
            else {}
        )

        broker_url = (
            mqtt_cfg.get("broker_url")
            or mqtt_cfg.get("broker")
        )

        if not broker_url or not mqtt_cfg.get("enabled", True):
            print("[MAIN] MQTT not configured or disabled.")
            return None

        try:
            return AggregatedMqttClient(
                broker_url=str(broker_url),
                client_id="game-manager",
            )

        except Exception as exc:
            print(f"[MAIN] MQTT unavailable: {exc}")
            return None

    # =========================================================
    # JSON-RPC REGISTRATION
    # =========================================================

    def _setup_jsonrpc(self):

        if self.mqtt_client is None:
            return

        handlers = {
            "game.change": self._rpc_change_game,
            "game.list": self._rpc_list_games,
            "game.status": self._rpc_status,
            "simulate_matrix": self._rpc_set_matrix_simulation,
            "simulate_input": self._rpc_set_input_simulation,
        }

        for method, handler in handlers.items():
            self.mqtt_client.register_rpc_handler(
                method,
                handler,
            )

        print("[MAIN] JSON-RPC handlers registered.")

    # =========================================================
    # BOOLEAN PARSING
    # =========================================================

    @staticmethod
    def _coerce_enabled_flag(params):

        if isinstance(params, dict):
            value = params.get(
                "enabled",
                params.get("value", False),
            )
        else:
            value = params

        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        if isinstance(value, str):
            value = value.strip().lower()

            if value in (
                "true", "1", "yes", "on", "enabled"
            ):
                return True

            if value in (
                "false", "0", "no", "off",
                "disabled", ""
            ):
                return False

        raise ValueError(
            f"Invalid simulation enabled value: {value!r}"
        )

    # =========================================================
    # SIMULATION RPC HANDLERS
    # =========================================================

    def _rpc_set_matrix_simulation(self, params):
        return self._set_simulation("matrix", params)

    def _rpc_set_input_simulation(self, params):
        return self._set_simulation("input", params)

    def _set_simulation(self, simulation_type, params):

        enabled = self._coerce_enabled_flag(params)

        engine_cfg = self.config.setdefault("engine", {})

        if simulation_type == "matrix":
            engine_cfg["simulate"] = enabled

        elif simulation_type == "input":
            engine_cfg["simulate_input"] = enabled

        else:
            raise ValueError(
                f"Unknown simulation type: {simulation_type}"
            )

        print(
            f"[RPC] {simulation_type} simulation requested: "
            f"{enabled}"
        )

        with self._game_lock:
            game = self.game

        if game is not None:

            if simulation_type == "matrix":
                game.set_simulate_matrix(enabled)
            else:
                game.set_simulate_input(enabled)

            print(
                "[RPC] Actual game simulation settings:",
                game.get_simulation_settings(),
            )

        else:
            print("[RPC] No game instance exists yet.")

        payload = self._publish_simulator_state()

        print("[RPC] Published simulator state:", payload)

        return {
            "enabled": enabled,
            "type": simulation_type,
        }

    # =========================================================
    # SIMULATOR STATE
    # =========================================================

    def _get_simulation_settings(self):

        engine_cfg = self.config.setdefault("engine", {})

        settings = {
            "simulateMatrix": bool(
                engine_cfg.get("simulate", False)
            ),
            "simulateInput": bool(
                engine_cfg.get("simulate_input", False)
            ),
        }

        with self._game_lock:
            game = self.game

        if game is not None:
            try:
                game_settings = game.get_simulation_settings()

                if isinstance(game_settings, dict):

                    settings["simulateMatrix"] = bool(
                        game_settings.get(
                            "simulateMatrix",
                            game_settings.get(
                                "simulate_matrix",
                                settings["simulateMatrix"],
                            ),
                        )
                    )

                    settings["simulateInput"] = bool(
                        game_settings.get(
                            "simulateInput",
                            game_settings.get(
                                "simulate_input",
                                settings["simulateInput"],
                            ),
                        )
                    )

            except Exception as exc:
                print(
                    "[MAIN] Could not read game simulation "
                    f"settings: {exc}"
                )

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
            "matrix": {
                "width": matrix_cols,
                "height": matrix_rows,
            },
            "camera": {
                "width": int(engine_cfg.get("width", 640)),
                "height": int(engine_cfg.get("height", 480)),
            },
        }

        self.mqtt_client.publish(
            SIMULATOR_STATE_TOPIC,
            payload,
            retain=True,
        )

        self.mqtt_client.publish(
            CAMERA_SIZE_TOPIC,
            payload["camera"],
            retain=True,
        )

        return payload

    def _publish_all_state(self):

        self._publish_available_games()
        self._publish_simulator_state()

    # =========================================================
    # GAME RPC HANDLERS
    # =========================================================

    def _rpc_change_game(self, params):

        game_name = (
            params.get("game")
            if isinstance(params, dict)
            else params
        )

        if not game_name:
            raise ValueError("Missing game name")

        game_name = str(game_name).strip().lower()

        if game_name not in GAME_FACTORIES:
            raise ValueError(
                f"Unsupported game '{game_name}'"
            )

        if not self.running:
            raise RuntimeError(
                "Application is not running"
            )

        # Queue the transition request.
        try:
            self._game_requests.put_nowait(game_name)

        except queue.Full:
            raise RuntimeError(
                "A game change is already pending"
            )

        # Ask the current game to exit its run loop.
        # Do not construct or replace games in this callback.
        with self._game_lock:
            current_game = self.game

        if current_game is not None:
            current_game.stop()

        print(
            f"[RPC] Game change accepted: {game_name}"
        )

        return {
            "game": game_name,
            "status": "accepted",
        }

    def _rpc_list_games(self, params):

        startup = self.config.get("startup", {})

        return {
            "games": startup.get(
                "available_games",
                ["tetris"],
            )
        }

    def _rpc_status(self, params):

        simulation = self._get_simulation_settings()

        with self._game_lock:
            game = self.game
            game_name = self.current_game_name

        return {
            "game": game_name,
            "running": (
                self.running
                and game is not None
                and getattr(game, "running", False)
            ),
            "simulation": simulation,
        }

    # =========================================================
    # GAME STATE PUBLISHING
    # =========================================================

    def _publish_available_games(self):

        if self.mqtt_client is None:
            return

        startup = self.config.get("startup", {})

        games = startup.get(
            "available_games",
            ["tetris"],
        )

        with self._game_lock:
            selected_game = self.current_game_name

        self.mqtt_client.publish(
            AVAILABLE_GAMES_TOPIC,
            {
                "games": games,
                "selectedGame": selected_game,
            },
            retain=True,
        )

    # =========================================================
    # GAME MANAGEMENT
    # =========================================================

    def _install_game(self, game_name):

        game_name = str(game_name).strip().lower()

        print(
            f"[MAIN] Creating game: {game_name}"
        )

        # This method is called by the application thread,
        # after the previous game's run() has returned.
        new_game = build_game(
            self.config,
            game_name,
            self.mqtt_client,
        )

        with self._game_lock:
            self.game = new_game
            self.current_game_name = game_name

        print(
            f"[MAIN] Current game: {game_name}"
        )

        self._publish_available_games()
        self._publish_simulator_state()

        return new_game

    def _process_game_request(self):

        try:
            game_name = self._game_requests.get_nowait()

        except queue.Empty:
            return False

        print(
            f"[MAIN] Processing game change: {game_name}"
        )

        # At this point, the previous game's run() has returned.
        # Its run() method should have completed its cleanup.

        with self._game_lock:
            self.game = None

        self._install_game(game_name)

        print(
            f"[MAIN] Game transition completed: {game_name}"
        )

        return True

    # =========================================================
    # APPLICATION LIFECYCLE
    # =========================================================

    def run(self, fps=None):

        if self.running:
            raise RuntimeError(
                "Application is already running"
            )

        target_fps = fps or get_fps(self.config)

        initial_game = (
            get_initial_game(self.config) or "tetris"
        )

        self._install_game(initial_game)

        self.running = True

        print("[MAIN] Application started.")

        try:
            while self.running:

                # Process transitions only in the application thread.
                if self._process_game_request():
                    continue

                with self._game_lock:
                    current_game = self.game
                    current_game_name = self.current_game_name

                if current_game is None:
                    continue

                print(
                    f"[MAIN] Running game: {current_game_name}"
                )

                # Blocking call. It must return when stop() is called.
                current_game.run(fps=target_fps)

                if not self.running:
                    break

                # A queued request explains why run() returned.
                if not self._game_requests.empty():
                    continue

                # No transition and no shutdown: unexpected exit.
                raise RuntimeError(
                    f"Game '{current_game_name}' exited "
                    "unexpectedly."
                )

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
                print(
                    "[MAIN] Error stopping game:",
                    exc,
                )


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":

    args = parse_args()

    manager = None

    try:
        config = load_config(args.config)

        if args.list_games:

            available = config.get(
                "startup",
                {},
            ).get(
                "available_games",
                ["tetris"],
            )

            print(
                "Available games:",
                ", ".join(available),
            )

        else:
            manager = GameManager(config=config)
            manager.run()

    except KeyboardInterrupt:
        print(
            "[MAIN] Keyboard interrupt received."
        )

    except Exception as exc:
        print(f"[ERROR] {exc}")
        raise

    finally:
        if manager is not None:
            manager.stop()

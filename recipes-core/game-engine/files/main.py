# main.py
from __future__ import annotations

from config import get_fps, get_initial_game, get_matrix_size, load_config
from games.test_game.test_game import MatrixGame
from games.tetris.tetris import Tetris
from mqtt_client import AggregatedMqttClient
from parse_arg import parse_args


SIMULATOR_STATE_TOPIC = "engine/simulator/config"
CAMERA_SIZE_TOPIC = "engine/camera/size"

GAME_FACTORIES = {
    "tetris": Tetris,
    "test_game": MatrixGame,
    "matrix_game": MatrixGame,
}


def build_game(config, game_name=None, mqtt_client=None):
    startup = config.get("startup", {})
    available_games = startup.get("available_games", ["tetris"])
    game_name = (game_name or get_initial_game(config) or "tetris").strip().lower()

    if game_name not in available_games and game_name not in GAME_FACTORIES:
        if "test_game" in available_games or "matrix_game" in available_games:
            game_name = "matrix_game"
        elif "tetris" in available_games:
            game_name = "tetris"
        else:
            raise ValueError(f"No supported game available in config: {available_games}")

    factory = GAME_FACTORIES.get(game_name)
    if factory is None:
        raise ValueError(f"Unsupported game '{game_name}'")

    return factory(config=config, mqtt_client=mqtt_client)


def select_game(config, mqtt_client=None):
    startup = config.get("startup", {})
    available_games = startup.get("available_games", ["tetris"])
    initial_game = get_initial_game(config)

    if initial_game in available_games and initial_game in GAME_FACTORIES:
        return build_game(config, initial_game, mqtt_client)

    if "test_game" in available_games or "matrix_game" in available_games:
        return build_game(config, "matrix_game", mqtt_client)

    if "tetris" in available_games:
        return build_game(config, "tetris", mqtt_client)

    raise ValueError(f"No supported game available in config: {available_games}")


class GameManager:
    def __init__(self, config, mqtt_client=None):
        self.config = config
        self.mqtt_client = mqtt_client or self._create_common_mqtt_client(config)
        self.game = None
        self.current_game_name = None
        self._setup_jsonrpc()
        if self.mqtt_client is not None:
            # Publishing right away would be dropped (not connected yet), so
            # publish whenever the connection comes up.
            self.mqtt_client.add_on_connect(self._publish_all_state)

    def _create_common_mqtt_client(self, config):
        mqtt_cfg = config.get("mqtt", {}) if isinstance(config, dict) else {}
        broker_url = mqtt_cfg.get("broker_url") or mqtt_cfg.get("broker")
        if not broker_url or not mqtt_cfg.get("enabled", True):
            print("[MAIN] MQTT not configured or disabled; running without MQTT.")
            return None

        try:
            return AggregatedMqttClient(broker_url=str(broker_url), client_id="game-manager")
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"[MAIN] MQTT unavailable ({exc}); continuing without RPC control.")
            return None

    def _setup_jsonrpc(self):
        if self.mqtt_client is None:
            return

        self.mqtt_client.register_rpc_handler("game.change", self._rpc_change_game)
        self.mqtt_client.register_rpc_handler("game.list", self._rpc_list_games)
        self.mqtt_client.register_rpc_handler("game.status", self._rpc_status)
        self.mqtt_client.register_rpc_handler("simulateMatrix", self._rpc_set_matrix_simulation)
        self.mqtt_client.register_rpc_handler("simulate_matrix", self._rpc_set_matrix_simulation)
        self.mqtt_client.register_rpc_handler("simulateInput", self._rpc_set_input_simulation)
        self.mqtt_client.register_rpc_handler("simulate_input", self._rpc_set_input_simulation)

    def _publish_all_state(self):
        self._publish_available_games()
        self._publish_simulator_state()

    def _rpc_set_matrix_simulation(self, params):
        enabled = self._coerce_enabled_flag(params)
        self.config.setdefault("engine", {})["simulate"] = enabled
        if self.game is not None:
            self.game.simulate_matrix_enabled = enabled
        self._publish_simulator_state()
        return {"enabled": enabled, "type": "matrix"}

    def _rpc_set_input_simulation(self, params):
        enabled = self._coerce_enabled_flag(params)
        self.config.setdefault("engine", {})["simulate_input"] = enabled
        if self.game is not None:
            self.game.simulate_input_enabled = enabled
        self._publish_simulator_state()
        return {"enabled": enabled, "type": "input"}

    @staticmethod
    def _coerce_enabled_flag(params):
        if isinstance(params, dict):
            value = params.get("enabled", params.get("value", False))
        else:
            value = params
        return bool(value)

    def _publish_simulator_state(self):
        if self.mqtt_client is None:
            return

        engine_cfg = self.config.setdefault("engine", {})
        matrix_rows, matrix_cols = get_matrix_size(self.config)
        payload = {
            "simulateMatrix": bool(engine_cfg.get("simulate", False)),
            "simulateInput": bool(engine_cfg.get("simulate_input", False)),
            "matrix": {"width": matrix_cols, "height": matrix_rows},
            "camera": {"width": int(engine_cfg.get("width", 640)), "height": int(engine_cfg.get("height", 480))},
        }
        self.mqtt_client.publish(SIMULATOR_STATE_TOPIC, payload, retain=True)
        self.mqtt_client.publish(CAMERA_SIZE_TOPIC, payload["camera"], retain=True)
        return payload

    def _rpc_change_game(self, params):
        game_name = params.get("game") if isinstance(params, dict) else params
        if not game_name:
            raise ValueError("Missing game name")
        self.change_game(str(game_name))
        return {"game": self.current_game_name, "status": "changed"}

    def _rpc_list_games(self, params):
        startup = self.config.get("startup", {})
        return {"games": startup.get("available_games", ["tetris"]) }

    def _rpc_status(self, params):
        return {"game": self.current_game_name, "running": self.game is not None and getattr(self.game, "running", False)}

    def _publish_available_games(self):
        if self.mqtt_client is None:
            return

        startup = self.config.get("startup", {})
        games = startup.get("available_games", ["tetris"])
        self.mqtt_client.publish(
            "engine/available",
            {"games": games, "selectedGame": self.current_game_name},
            retain=True,
        )

    def change_game(self, game_name):
        game_name = str(game_name).strip().lower()
        if game_name not in GAME_FACTORIES:
            raise ValueError(f"Unsupported game '{game_name}'")

        if self.game is not None:
            try:
                self.game.stop()
            except Exception:
                pass

        self.game = build_game(self.config, game_name, self.mqtt_client)
        self.current_game_name = game_name
        self._publish_available_games()
        return self.game

    def run(self, fps=None):
        if self.game is None:
            self.current_game_name = get_initial_game(self.config) or "tetris"
            self.game = select_game(self.config, self.mqtt_client)
            self._publish_available_games()

        self.game.run(fps=fps or get_fps(self.config))


if __name__ == "__main__":
    args = parse_args()

    try:
        config = load_config(args.config)

        if args.list_games:
            available = config.get("startup", {}).get("available_games", ["tetris"])
            print("Available games:", ", ".join(available))
        else:
            manager = GameManager(config=config)
            manager.run()

    except Exception as e:
        print(f"[ERROR] {e}")

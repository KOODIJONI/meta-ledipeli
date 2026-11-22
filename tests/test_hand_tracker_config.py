import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "recipes-core" / "hand-tracker" / "files" / "config.py"
GAME_ENGINE_CONFIG_PATH = Path(__file__).resolve().parents[1] / "recipes-core" / "game-engine" / "files" / "config.py"

spec = importlib.util.spec_from_file_location("hand_tracker_config_module", CONFIG_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
load_config = module.load_config

engine_spec = importlib.util.spec_from_file_location("game_engine_config_module", GAME_ENGINE_CONFIG_PATH)
engine_module = importlib.util.module_from_spec(engine_spec)
engine_spec.loader.exec_module(engine_module)
get_matrix_size = engine_module.get_matrix_size


class HandTrackerConfigTests(unittest.TestCase):
    def test_load_config_supports_recognizer_root(self):
        config_data = {
            "recognizer": {
                "debug": True,
                "model": {"path": "/tmp/model.task"},
                "ipc": {"socket_path": "/tmp/test.sock"},
                "recognition": {
                    "num_hands": 2,
                    "min_hand_detection_confidence": 0.5,
                    "min_hand_presence_confidence": 0.5,
                    "min_tracking_confidence": 0.5,
                },
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "hand_tracker_config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            config = load_config(config_path)

            self.assertTrue(config["recognizer"]["debug"])
            self.assertEqual(config["recognizer"]["model"]["path"], "/tmp/model.task")
            self.assertEqual(config["recognizer"]["ipc"]["socket_path"], "/tmp/test.sock")
            self.assertEqual(config["recognizer"]["recognition"]["num_hands"], 2)

    def test_game_engine_uses_matrix_config_dimensions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_cfg_path = Path(tmpdir) / "matrix_config.json"
            matrix_cfg_path.write_text(
                json.dumps({"tile_rows": 8, "tile_cols": 8, "grid_rows": 6, "grid_cols": 6}),
                encoding="utf-8",
            )

            config = {
                "engine": {
                    "matrix_config_path": str(matrix_cfg_path),
                    "matrix_rows": 8,
                    "matrix_cols": 8,
                }
            }

            self.assertEqual(get_matrix_size(config), (48, 48))


if __name__ == "__main__":
    unittest.main()

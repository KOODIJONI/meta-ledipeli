import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

hand_client_module = types.ModuleType("hand_client")

class DummyTracker:
    def __init__(self, socket_path=None):
        self.socket_path = socket_path

    def stop(self):
        return None

    def get_latest_state(self):
        return None

hand_client_module.HandTrackerClient = DummyTracker
sys.modules.setdefault("hand_client", hand_client_module)

ledmatrix_module = types.ModuleType("ledmatrix")
ledmatrix_module.LEDMatrix = None
sys.modules.setdefault("ledmatrix", ledmatrix_module)

from games.base_game import BaseGame, Gesture


class GestureBehaviorTests(unittest.TestCase):
    def test_get_hand_gesture_returns_enum_member(self):
        game = BaseGame(socket_path="/tmp/hand_tracker.sock", config={})

        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "open"}]}), Gesture.OPEN)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "closed"}]}), Gesture.CLOSED)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "pointing"}]}), Gesture.POINTING)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "unknown"}]}), Gesture.UNKNOWN)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "Open_Palm"}]}), Gesture.OPEN)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "Closed_Fist"}]}), Gesture.CLOSED)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": "Pointing_Up"}]}), Gesture.POINTING)
        self.assertIs(game.get_hand_gesture({"hands": [{"gesture": None}]}), Gesture.UNKNOWN)
        self.assertIs(game.get_hand_gesture({"hands": [{}]}), Gesture.UNKNOWN)


if __name__ == "__main__":
    unittest.main()

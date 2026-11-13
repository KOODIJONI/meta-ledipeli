# games/base_game.py
import time
from enum import Enum

try:
    from ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover - hardware module may be absent in dev/test envs
    LEDMatrix = None

from config import get_hand_tracker_socket, get_matrix_size, get_window_size
from hand_client import HandTrackerClient

class Gesture(Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    POINTING = "pointing"


class BaseGame:
    def __init__(self, socket_path=None, config=None):
        """Shared game initialization: boots up the hand tracker client once."""
        self.config = config or {}
        if socket_path is None:
            socket_path = get_hand_tracker_socket(self.config)

        self.rows, self.cols = get_matrix_size(self.config)
        self.width, self.height = get_window_size(self.config)

        self.led_matrix = None
        self._init_led_matrix()

        print("[BASE] Initializing HandTrackerClient...")
        self.tracker = HandTrackerClient(socket_path=str(socket_path))
        self.running = True

    def get_display_size(self):
        return self.width, self.height

    def get_hand_position(self, hand_state, index=0):
        """Return the wrist position for a specific hand as normalized x/y values."""
        hands = hand_state.get("hands", []) if isinstance(hand_state, dict) else []
        if index >= len(hands):
            return None

        hand = hands[index]
        wrist = hand.get("wrist", {}) if isinstance(hand, dict) else {}
        x = float(wrist.get("x", 0.0))
        y = float(wrist.get("y", 0.0))

        max_w = float(self.width)
        max_h = float(self.height)
        if x > 1.0 or y > 1.0:
            norm_x = min(max(x / max_w, 0.0), 1.0)
            norm_y = min(max(y / max_h, 0.0), 1.0)
        else:
            norm_x = min(max(x, 0.0), 1.0)
            norm_y = min(max(y, 0.0), 1.0)

        return norm_x, norm_y

    def get_hand_gesture(self, hand_state, index=0):
        """Return the last known gesture for a specific hand if available."""
        hands = hand_state.get("hands", []) if isinstance(hand_state, dict) else []
        if index >= len(hands):
            return Gesture.UNKNOWN.value

        hand = hands[index]
        return str(hand.get("gesture", Gesture.UNKNOWN.value)).lower()

    def _init_led_matrix(self):
        """Initialize the hardware LED matrix when the driver is available."""
        engine_cfg = self.config.get("engine", {}) if isinstance(self.config, dict) else {}
        if not bool(engine_cfg.get("use_led_matrix", True)):
            print("[BASE] LED matrix disabled by config.")
            return

        if LEDMatrix is None:
            print("[BASE] LED matrix module unavailable; terminal rendering only.")
            return

        try:
            self.led_matrix = LEDMatrix()
            self.rows = int(self.led_matrix.rows)
            self.cols = int(self.led_matrix.cols)
            self.clear_led_matrix()
            print(f"[BASE] LED matrix ready: {self.led_matrix.rows}x{self.led_matrix.cols}")
        except Exception as exc:  # pragma: no cover - hardware may not be attached in CI/dev
            print(f"[BASE] LED matrix unavailable ({exc}); falling back to terminal rendering.")
            self.led_matrix = None

    def clear_led_matrix(self, r=0, g=0, b=0):
        """Clear the in-memory matrix buffer for the next frame."""
        if self.led_matrix is None:
            return False

        try:
            return self.led_matrix.fill(r, g, b) == 0
        except Exception:
            return False

    def set_led_pixel(self, x, y, r=255, g=255, b=255):
        """Write a single pixel to the LED matrix using board coordinates."""
        if self.led_matrix is None:
            return False

        try:
            return self.led_matrix.set_pixel(x, y, r, g, b) == 0
        except Exception:
            return False

    def flush_led_matrix(self):
        """Push the current matrix buffer to the driver if available."""
        if self.led_matrix is None:
            return False

        try:
            result = self.led_matrix.flush()
            return result in (None, 0, -1)
        except Exception:
            return False

    def handle_input(self, hand_state):
        """Override this in child games to process hand gestures/coordinates."""
        raise NotImplementedError("Child games must implement handle_input()")

    def update(self):
        """Override this for game logic updates per tick."""
        pass

    def render(self):
        """Override this to draw the game screen."""
        pass

    def run(self, fps=60):
        """Main game loop shared across all games."""
        print(f"[BASE] Starting game loop... Press Ctrl+C to exit.")
        frame_delay = 1.0 / fps

        try:
            while self.running:
                start_time = time.time()

                hand_state = self.tracker.get_latest_state()
                if hand_state:
                    self.handle_input(hand_state)

                self.update()

                self.clear_led_matrix()
                self.render()
                self.flush_led_matrix()

                elapsed = time.time() - start_time
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)

        except KeyboardInterrupt:
            print("\n[BASE] Stopping game...")
        finally:
            self.tracker.stop()
            print("[BASE] Tracker stopped. Exiting cleanly.")


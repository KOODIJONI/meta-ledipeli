#base_game/base_game.py
from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable

try:
    from ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover - hardware module may be absent in dev/test envs
    LEDMatrix = None

from config import get_hand_tracker_socket, get_matrix_size, get_window_size, get_hand_tracker_socket
from .game_mqtt_bridge import GameMqttBridge
from hand_client import HandTrackerClient
from base_game.animation_player import RawBinAnimationPlayer
import threading


class Gesture(Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    POINTING = "pointing"
    VICTORY = "victory"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"

aliases = {
    "unknown": Gesture.UNKNOWN,
    "none": Gesture.UNKNOWN,
    "open": Gesture.OPEN,
    "open_palm": Gesture.OPEN,
    "open_hand": Gesture.OPEN,
    "closed": Gesture.CLOSED,
    "closed_fist": Gesture.CLOSED,
    "fist": Gesture.CLOSED,
    "pointing": Gesture.POINTING,
    "pointing_up": Gesture.POINTING,
    "point_up": Gesture.POINTING,
    "thumb_up": Gesture.THUMBS_UP,
    "thumb_down": Gesture.THUMBS_DOWN,
    "victory": Gesture.VICTORY,
}


class BaseGame:
    def __init__(self, socket_path=None, config=None, mqtt_client=None, mqtt_broker=None, state_prefix: str = "game", tracker=None):
        """Shared game initialization: accepts a shared hand tracker client."""
        self.config = config or {}
        self.rows, self.cols = get_matrix_size(self.config)
        self.width, self.height = get_window_size(self.config)

        self._shadow = bytearray(self.rows * self.cols * 3)
        debug_cfg = self.config.get("debug", {}) if isinstance(self.config, dict) else {}

        self.debug_enabled = bool(debug_cfg.get("show_fps", False) or debug_cfg.get("debug", False))
        self._fps_window_start = time.monotonic()
        self._fps_frame_count = 0

        self.anim_player = RawBinAnimationPlayer("/usr/bin/game-engine/assets/screensaver_1.bin", self.cols, self.rows)

        self.state_prefix = state_prefix
        self._mqtt_bridge = GameMqttBridge(
            config=self.config,
            state_prefix=state_prefix,
            mqtt_client=mqtt_client,
            broker_url=mqtt_broker,
            width=self.width,
            height=self.height,
        )

        self._cleanup_lock = threading.Lock()
        self._cleaned_up = False    
        self.led_matrix = None
        self._init_led_matrix()

        # Use shared tracker if provided, otherwise fallback to local instance
        if tracker is not None:
            print("[BASE] Using shared central HandTrackerClient.")
            self.tracker = tracker
        else:
            print("[BASE] Initializing local HandTrackerClient...")
            if socket_path is None:
                socket_path = get_hand_tracker_socket(self.config)
            self.tracker = HandTrackerClient(socket_path=str(socket_path))
            
        self.running = True
    @property
    def mqtt(self):
        return self._mqtt_bridge.client

    @property
    def shared_state(self) -> dict[str, Any]:
        return self._mqtt_bridge.shared_state

    @property
    def simulate_matrix_enabled(self) -> bool:
        return self._mqtt_bridge.simulate_matrix_enabled

    @property
    def simulate_input_enabled(self) -> bool:
        return self._mqtt_bridge.simulate_input_enabled

    def set_shared_state(self, key: str, value: Any):
        return self._mqtt_bridge.set_shared_state(key, value)

    def get_shared_state(self, key: str, default: Any = None):
        return self._mqtt_bridge.get_shared_state(key, default)

    def publish_state(self, payload: Any | None = None, topic: str | None = None):
        return self._mqtt_bridge.publish_state(payload, topic)

    def subscribe_to_state(self, topic: str, callback: Callable[[Any, str], None]):
        return self._mqtt_bridge.subscribe_to_state(topic, callback)

    def call_rpc(self, method: str, params: Any | None = None, timeout_ms: int = 5000):
        return self._mqtt_bridge.call_rpc(method, params=params, timeout_ms=timeout_ms)
    def _sync_shadow_from_matrix(self):
        """Refresh the shadow buffer from the hardware matrix (GRB bytes).

        Falls back to the manually written shadow if there is no hardware or the read fails.
        """
        if self.led_matrix is None:
            return False

        try:
            raw = self.led_matrix.get_raw_frame()
        except Exception:
            return False

        if len(raw) != len(self._shadow):
            return False

        self._shadow[:] = raw
        return True

    def publish_simulated_matrix(self):
        """Publish the current frame in raw GRB bytes for the browser simulator."""
        self._sync_shadow_from_matrix()
        return self._mqtt_bridge.publish_matrix(bytes(self._shadow), self.cols, self.rows)
    # -- Hand input -----------------------------------------------------------

    def _get_latest_hand_state(self):
        if self.simulate_input_enabled:
            return self._mqtt_bridge.simulated_hand_state
        return self.tracker.get_latest_state()

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
            return Gesture.UNKNOWN

        hand = hands[index]
        gesture = hand.get("gesture", Gesture.UNKNOWN.value) if isinstance(hand, dict) else Gesture.UNKNOWN.value
        print(f"[DEBUG] Raw hand gesture for index {index}: {gesture!r}")

        if isinstance(gesture, Gesture):
            return gesture

        if hasattr(gesture, "value"):
            gesture = gesture.value

        normalized = str(gesture).strip().lower()
        normalized = normalized.replace("-", "_").replace(" ", "_")

        if normalized in aliases:
            return aliases[normalized]

        for candidate in Gesture:
            if candidate.value == normalized:
                return candidate

        return Gesture.UNKNOWN

    # -- LED matrix -----------------------------------------------------------

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
            self._shadow = bytearray(self.rows * self.cols * 3)
            self.clear_led_matrix()
            print(f"[BASE] LED matrix ready: {self.led_matrix.rows}x{self.led_matrix.cols}")
        except Exception as exc:  # pragma: no cover - hardware may not be attached in CI/dev
            print(f"[BASE] LED matrix unavailable ({exc}); falling back to terminal rendering.")
            self.led_matrix = None

    def clear_led_matrix(self, r=0, g=0, b=0):
        """Clear the in-memory matrix buffer for the next frame."""
        self._shadow[:] = bytes((g & 0xFF, r & 0xFF, b & 0xFF)) * (self.rows * self.cols)

        if self.led_matrix is None:
            return False

        try:
            return self.led_matrix.fill(r, g, b) == 0
        except Exception:
            return False

    def fill(self, r=0, g=0, b=0):
        """Fill the entire LED matrix via the C driver."""
        if self.led_matrix is not None:
            try:
                self.led_matrix.fill(r, g, b)
            except Exception:
                pass

    def fill_rect(self, x1, y1, x2, y2, r=255, g=255, b=255):
        """Draw a filled rectangle via the C driver."""
        if self.led_matrix is not None:
            try:
                self.led_matrix.fill_rect(x1, y1, x2, y2, r, g, b)
            except Exception:
                pass

    def draw_line(self, x1, y1, x2, y2, r=255, g=255, b=255):
        """Draw a line via the C driver."""
        if self.led_matrix is not None:
            try:
                self.led_matrix.draw_line(int(x1), int(y1), int(x2), int(y2), r, g, b)
            except Exception:
                pass

    def set_led_pixel(self, x, y, r=255, g=255, b=255):
        """Write a single pixel via the C driver."""
        if self.led_matrix is not None:
            try:
                self.led_matrix.set_pixel(int(x), int(y), r, g, b)
            except Exception:
                pass


    def flush_led_matrix(self):
        """Push the current matrix buffer to the driver if available."""
        if self.led_matrix is None:
            return False

        try:
            result = self.led_matrix.flush()
            return result in (None, 0, -1)
        except Exception:
            return False

    # -- Game loop ------------------------------------------------------------

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
        print("[BASE] Starting game loop... Press Ctrl+C to exit.")
        frame_delay = 1.0 / fps

        try:
            while self.running:
                start = time.monotonic()

                t0 = time.monotonic()
                hand_state = self._get_latest_hand_state()
                if hand_state:
                    self.handle_input(hand_state)
                input_time = time.monotonic() - t0

                t0 = time.monotonic()
                self.update()
                update_time = time.monotonic() - t0

                t0 = time.monotonic()
                self.clear_led_matrix()
                self.render()
                render_time = time.monotonic() - t0

                t0 = time.monotonic()
                self.publish_simulated_matrix()
                mqtt_time = time.monotonic() - t0

                t0 = time.monotonic()
                flush_result = self.flush_led_matrix()
                flush_time = time.monotonic() - t0

                total_time = time.monotonic() - start

                if self.config.get("debug", {}).get("show_fps", False):
                    print(
                        f"[TIMING] input={input_time*1000:.1f}ms "
                        f"update={update_time*1000:.1f}ms "
                        f"render={render_time*1000:.1f}ms "
                        f"mqtt={mqtt_time*1000:.1f}ms "
                        f"flush={flush_time*1000:.1f}ms "
                        f"total={total_time*1000:.1f}ms "
                        f"flush_result={flush_result}"
                    )
                    self._update_debug_fps(flush_result)

                frame_delay = 1.0 / fps
                remaining = frame_delay - total_time
                if remaining > 0:
                    time.sleep(remaining)

        except KeyboardInterrupt:
            print("\n[BASE] Stopping game...")
        finally:
            self._cleanup()


    def set_simulate_matrix(self, enabled: bool):
        return self._mqtt_bridge.set_simulate_matrix_enabled(enabled)

    def set_simulate_input(self, enabled: bool):
        return self._mqtt_bridge.set_simulate_input_enabled(enabled)

    def get_simulation_settings(self):
        return self._mqtt_bridge.get_simulation_settings()

    def _update_debug_fps(self, frame_succeeded: bool):
        if not self.debug_enabled:
            return

        if not frame_succeeded:
            return

        self._fps_frame_count += 1
        elapsed = time.monotonic() - self._fps_window_start
        if elapsed >= 1.0:
            fps = self._fps_frame_count / elapsed
            print(f"[DEBUG] FPS: {fps:.1f}")
            self._fps_window_start = time.monotonic()
            self._fps_frame_count = 0
            
    def set_brightness(self, brightness: float) -> bool:
        if self.led_matrix is None:
            return False
        try:
            return self.led_matrix.set_brightness(brightness) == 0
        except Exception as exc:
            print(f"[BASE] Failed to set brightness: {exc}")
            return False


    def stop(self):
        """Safe from any thread: only asks the loop to exit."""
        self.running = False

    def _cleanup(self):
        """Runs once, on the game thread, after the loop has exited."""
        with self._cleanup_lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True

        led, self.led_matrix = self.led_matrix, None
        if led is not None:
            try:
                led.close()
            except Exception as exc:
                print(f"[BASE] Error closing LED matrix: {exc}")

        self._mqtt_bridge.stop()
        print("[BASE] Game cleaned up.")


    def pause():
        pass
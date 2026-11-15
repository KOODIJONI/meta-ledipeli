# games/base_game.py
from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable

try:
    from ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover - hardware module may be absent in dev/test envs
    LEDMatrix = None

from config import get_hand_tracker_socket, get_matrix_size, get_window_size
from hand_client import HandTrackerClient
from mqtt_client import AggregatedMqttClient

class Gesture(Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    POINTING = "pointing"
    VICTORY = "victory"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class BaseGame:
    def __init__(self, socket_path=None, config=None, mqtt_client=None, mqtt_broker=None, state_prefix: str = "game"):
        """Shared game initialization: boots up the hand tracker client once."""
        self.config = config or {}
        if socket_path is None:
            socket_path = get_hand_tracker_socket(self.config)

        self.rows, self.cols = get_matrix_size(self.config)
        self.width, self.height = get_window_size(self.config)
        # Own copy of the frame (GRB, row-major) for the browser simulator,
        # because the driver's get_raw_frame() fails with error code -2.
        self._shadow = bytearray(self.rows * self.cols * 3)

        engine_cfg = self.config.get("engine", {}) if isinstance(self.config, dict) else {}
        self.simulate_matrix_enabled = bool(engine_cfg.get("simulate", False))
        self.simulate_input_enabled = bool(engine_cfg.get("simulate_input", False))

        self.state_prefix = state_prefix
        self.shared_state: dict[str, Any] = {}
        self.mqtt = None
        self._mqtt_client = mqtt_client
        self._unsub_mouse = None
        self._last_sim_error_time = 0.0
        self._simulated_mouse = {
            "x": 0.5,
            "y": 0.5,
            "gesture": Gesture.POINTING.value,
        }
        self._simulated_hand_state = self._build_simulated_hand_state(self._simulated_mouse)
        self._init_mqtt_client(broker_url=mqtt_broker)

        self.led_matrix = None
        self._init_led_matrix()

        print("[BASE] Initializing HandTrackerClient...")
        self.tracker = HandTrackerClient(socket_path=str(socket_path))
        self.running = True

    def _init_mqtt_client(self, broker_url=None):
        """Initialize an optional shared MQTT pub/sub bridge for cross-instance state."""
        if self._mqtt_client is not None:
            self.mqtt = self._mqtt_client
            self._attach_simulated_input_listener()
            return self.mqtt

        mqtt_cfg = self.config.get("mqtt", {}) if isinstance(self.config, dict) else {}
        broker_url = broker_url or mqtt_cfg.get("broker_url") or mqtt_cfg.get("broker")
        if not broker_url:
            return None

        enabled = bool(mqtt_cfg.get("enabled", True))
        if not enabled:
            return None

        try:
            self.mqtt = AggregatedMqttClient(broker_url=str(broker_url), client_id=f"game-{id(self)}")
            self._attach_simulated_input_listener()
            print(f"[BASE] MQTT client ready: {broker_url}")
            return self.mqtt
        except Exception as exc:  # pragma: no cover - optional external service
            print(f"[BASE] MQTT unavailable ({exc}); continuing without it.")
            self.mqtt = None
            return None

    def _attach_simulated_input_listener(self):
        if self.mqtt is None:
            return

        def _on_mouse_message(message, topic):
            if not self.simulate_input_enabled:
                return

            payload = message
            if isinstance(payload, (bytes, bytearray)):
                payload = payload.decode("utf-8", errors="ignore")

            try:
                if isinstance(payload, str):
                    parsed = __import__("json").loads(payload)
                else:
                    parsed = payload
            except Exception:
                return

            if not isinstance(parsed, dict):
                return

            x = float(parsed.get("x", self._simulated_mouse.get("x", 0.5)))
            y = float(parsed.get("y", self._simulated_mouse.get("y", 0.5)))
            # The web GUI sends camera pixels; convert to normalized 0..1.
            if x > 1.0 or y > 1.0:
                x /= float(self.width)
                y /= float(self.height)

            self._simulated_mouse = {
                "x": x,
                "y": y,
                "gesture": str(parsed.get("gesture", self._simulated_mouse.get("gesture", Gesture.POINTING.value))),
            }
            self._simulated_hand_state = self._build_simulated_hand_state(self._simulated_mouse)

        self._unsub_mouse = self.mqtt.subscribe("engine/mouse", _on_mouse_message)

    def _build_simulated_hand_state(self, mouse_state):
        if not isinstance(mouse_state, dict):
            mouse_state = self._simulated_mouse

        x = float(mouse_state.get("x", 0.5))
        y = float(mouse_state.get("y", 0.5))
        gesture = mouse_state.get("gesture", Gesture.POINTING.value)

        normalized_x = min(max(x, 0.0), 1.0)
        normalized_y = min(max(y, 0.0), 1.0)

        return {
            "hands": [{
                "wrist": {"x": normalized_x, "y": normalized_y},
                "gesture": str(gesture).strip().lower(),
            }]
        }

    def _get_latest_hand_state(self):
        if self.simulate_input_enabled:
            return self._simulated_hand_state
        return self.tracker.get_latest_state()

    def set_shared_state(self, key: str, value: Any):
        self.shared_state[key] = value
        if self.mqtt is not None:
            self.mqtt.publish_state(f"{self.state_prefix}/{key}", value)
        return value

    def get_shared_state(self, key: str, default: Any = None):
        return self.shared_state.get(key, default)

    def publish_state(self, payload: Any | None = None, topic: str | None = None):
        if payload is None:
            payload = self.shared_state
        target_topic = topic or f"{self.state_prefix}/state"
        if self.mqtt is not None:
            self.mqtt.publish_state(target_topic, payload)
        return payload

    def subscribe_to_state(self, topic: str, callback: Callable[[Any, str], None]):
        if self.mqtt is None:
            return None
        return self.mqtt.subscribe_state(topic, callback)

    def call_rpc(self, method: str, params: Any | None = None, timeout_ms: int = 5000):
        if self.mqtt is None:
            raise RuntimeError("MQTT JSON-RPC client is not configured")
        return self.mqtt.call(method, params=params, timeout_ms=timeout_ms)

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
            "victory" : Gesture.VICTORY
            
        }

        if normalized in aliases:
            return aliases[normalized]

        for candidate in Gesture:
            if candidate.value == normalized:
                return candidate

        return Gesture.UNKNOWN

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

    def set_led_pixel(self, x, y, r=255, g=255, b=255):
        """Write a single pixel to the LED matrix using board coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            index = (int(y) * self.cols + int(x)) * 3
            self._shadow[index:index + 3] = bytes((g & 0xFF, r & 0xFF, b & 0xFF))

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

    def publish_simulated_matrix(self):
        """Publish the current frame in raw GRB bytes for the browser simulator."""
        if self.mqtt is None:
            return False

        if not self.simulate_matrix_enabled:
            return False

        try:
            frame = bytes(self._shadow)
            size_payload = {
                "width": int(self.cols),
                "height": int(self.rows),
            }
            self.mqtt.publish("engine/matrix/size", size_payload)
            self.mqtt.publish("engine/matrix/data", frame)
            return True
        except Exception as exc:  # pragma: no cover - runtime hardware path only
            now = time.time()
            if now - self._last_sim_error_time > 5.0:
                self._last_sim_error_time = now
                print(f"[BASE] Failed to publish simulated matrix frame: {exc}")
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

                hand_state = self._get_latest_hand_state()
                
                if hand_state:
                    self.handle_input(hand_state)

                self.update()

                self.clear_led_matrix()
                self.render()

                self.publish_simulated_matrix()
                self.flush_led_matrix()

                elapsed = time.time() - start_time
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)

        except KeyboardInterrupt:
            print("\n[BASE] Stopping game...")
        finally:
            self.stop()

    def stop(self):
        """Stop the tracker, MQTT bridge, and running loop cleanly."""
        self.running = False

        if hasattr(self, "tracker") and self.tracker is not None:
            try:
                self.tracker.stop()
            except Exception:
                pass

        if self._unsub_mouse is not None:
            try:
                self._unsub_mouse()
            except Exception:
                pass
            self._unsub_mouse = None

        # Only stop the MQTT client if this game created it; a client passed
        # in by GameManager is shared and must stay alive across game changes.
        if self.mqtt is not None and self._mqtt_client is None:
            try:
                self.mqtt.stop()
            except Exception:
                pass

        print("[BASE] Tracker stopped. Exiting cleanly.")
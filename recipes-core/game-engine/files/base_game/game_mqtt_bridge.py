from __future__ import annotations

import json
import time
from typing import Any, Callable

from mqtt_client import AggregatedMqttClient

DEFAULT_GESTURE = "pointing"


class GameMqttBridge:
    """Everything MQTT-related for a game: shared state, RPC, simulated mouse
    input and simulated matrix output. BaseGame owns one instance of this."""

    def __init__(
        self,
        config: dict | None = None,
        state_prefix: str = "game",
        mqtt_client=None,
        broker_url: str | None = None,
        width: int = 1,
        height: int = 1,
    ):
        self.config = config or {}
        self.state_prefix = state_prefix
        self.width = width
        self.height = height

        engine_cfg = self.config.get("engine", {}) if isinstance(self.config, dict) else {}
        self.simulate_matrix_enabled = bool(engine_cfg.get("simulate", False))
        self.simulate_input_enabled = bool(engine_cfg.get("simulate_input", False))

        self.shared_state: dict[str, Any] = {}
        self.client = None
        self._external_client = mqtt_client
        self._unsub_mouse = None
        self._last_sim_error_time = 0.0

        self._simulated_mouse = {"x": 0.5, "y": 0.5, "gesture": DEFAULT_GESTURE}
        self.simulated_hand_state = self._build_simulated_hand_state(self._simulated_mouse)

        self._init_client(broker_url)

    def _init_client(self, broker_url=None):
        """Initialize an optional shared MQTT pub/sub bridge for cross-instance state."""
        if self._external_client is not None:
            self.client = self._external_client
            self._attach_simulated_input_listener()
            return self.client

        mqtt_cfg = self.config.get("mqtt", {}) if isinstance(self.config, dict) else {}
        broker_url = broker_url or mqtt_cfg.get("broker_url") or mqtt_cfg.get("broker")
        if not broker_url:
            return None

        if not bool(mqtt_cfg.get("enabled", True)):
            return None

        try:
            self.client = AggregatedMqttClient(broker_url=str(broker_url), client_id=f"game-{id(self)}")
            self._attach_simulated_input_listener()
            print(f"[BASE] MQTT client ready: {broker_url}")
            return self.client
        except Exception as exc:  # pragma: no cover - optional external service
            print(f"[BASE] MQTT unavailable ({exc}); continuing without it.")
            self.client = None
            return None
    def _attach_simulated_input_listener(self):
        if self.client is None:
            print("[SIM INPUT] No MQTT client available")
            return

        def _on_mouse_message(message, topic):
            print(
                f"[SIM INPUT] Received topic={topic}, "
                f"enabled={self.simulate_input_enabled}, "
                f"message={message!r}"
            )

            if not self.simulate_input_enabled:
                print("[SIM INPUT] Ignored: simulation is disabled")
                return

            payload = message

            if isinstance(payload, (bytes, bytearray)):
                payload = payload.decode("utf-8", errors="ignore")

            try:
                parsed = json.loads(payload) if isinstance(payload, str) else payload
            except Exception as exc:
                print(f"[SIM INPUT] JSON parsing failed: {exc}")
                return

            if not isinstance(parsed, dict):
                print(f"[SIM INPUT] Invalid payload: {parsed!r}")
                return

            try:
                x = float(parsed.get("x", 0.5))
                y = float(parsed.get("y", 0.5))

                if x > 1.0 or y > 1.0:
                    x /= float(self.width)
                    y /= float(self.height)

                x = min(max(x, 0.0), 1.0)
                y = min(max(y, 0.0), 1.0)

                gesture = str(
                    parsed.get("gesture", DEFAULT_GESTURE)
                ).strip().lower()

                self._simulated_mouse = {
                    "x": x,
                    "y": y,
                    "gesture": gesture,
                }

                self.simulated_hand_state = (
                    self._build_simulated_hand_state(self._simulated_mouse)
                )

                print(
                    "[SIM INPUT] Updated hand state:",
                    self.simulated_hand_state
                )

            except (TypeError, ValueError, ZeroDivisionError) as exc:
                print(f"[SIM INPUT] Invalid coordinates: {exc}")

        self._unsub_mouse = self.client.subscribe(
            "engine/mouse",
            _on_mouse_message
        )

    print("[SIM INPUT] Subscribed to engine/mouse")
    def _build_simulated_hand_state(self, mouse_state):
        if not isinstance(mouse_state, dict):
            mouse_state = self._simulated_mouse

        x = float(mouse_state.get("x", 0.5))
        y = float(mouse_state.get("y", 0.5))
        gesture = mouse_state.get("gesture", DEFAULT_GESTURE)

        return {
            "hands": [{
                "wrist": {"x": min(max(x, 0.0), 1.0), "y": min(max(y, 0.0), 1.0)},
                "gesture": str(gesture).strip().lower(),
            }]
        }


    def set_shared_state(self, key: str, value: Any):
        self.shared_state[key] = value
        if self.client is not None:
            self.client.publish_state(f"{self.state_prefix}/{key}", value)
        return value

    def get_shared_state(self, key: str, default: Any = None):
        return self.shared_state.get(key, default)

    def publish_state(self, payload: Any | None = None, topic: str | None = None):
        if payload is None:
            payload = self.shared_state
        target_topic = topic or f"{self.state_prefix}/state"
        if self.client is not None:
            self.client.publish_state(target_topic, payload)
        return payload

    def subscribe_to_state(self, topic: str, callback: Callable[[Any, str], None]):
        if self.client is None:
            return None
        return self.client.subscribe_state(topic, callback)

    def call_rpc(self, method: str, params: Any | None = None, timeout_ms: int = 5000):
        if self.client is None:
            raise RuntimeError("MQTT JSON-RPC client is not configured")
        return self.client.call(method, params=params, timeout_ms=timeout_ms)

    def publish_matrix(self, frame: bytes, cols: int, rows: int) -> bool:
        """Publish a raw GRB frame for the browser simulator."""
        if self.client is None or not self.simulate_matrix_enabled:
            return False

        try:
            self.client.publish("engine/matrix/size", {"width": int(cols), "height": int(rows)})
            self.client.publish("engine/matrix/data", frame)
            return True
        except Exception as exc:  # pragma: no cover - runtime hardware path only
            now = time.time()
            if now - self._last_sim_error_time > 5.0:
                self._last_sim_error_time = now
                print(f"[BASE] Failed to publish simulated matrix frame: {exc}")
            return False

    def stop(self):
        if self._unsub_mouse is not None:
            try:
                self._unsub_mouse()
            except Exception:
                pass
            self._unsub_mouse = None

        if self.client is not None and self._external_client is None:
            try:
                self.client.stop()
            except Exception:
                pass

    def set_simulate_matrix_enabled(self, enabled: bool):
        self.simulate_matrix_enabled = bool(enabled)
        return self.get_simulation_settings()

    def set_simulate_input_enabled(self, enabled: bool):
        self.simulate_input_enabled = bool(enabled)
        return self.get_simulation_settings()

    def get_simulation_settings(self):
        return {
            "simulate_matrix": self.simulate_matrix_enabled,
            "simulate_input": self.simulate_input_enabled,
        }
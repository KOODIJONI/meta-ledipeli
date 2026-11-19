from __future__ import annotations

import json
import threading
import time
import uuid
from collections import defaultdict
from concurrent.futures import Future
from typing import Any, Callable

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional dependency in lightweight environments
    mqtt = None


class MqttRpcError(RuntimeError):
    """Raised when a JSON-RPC request fails."""

    def __init__(self, message: str, code: int | None = None, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data


class AggregatedMqttClient:
    """Small MQTT pub/sub client with JSON-RPC 2.0 request/response handling."""

    def __init__(
        self,
        broker_url: str = "tcp://localhost:1883",
        client_id: str | None = None,
        request_topic: str = "engine/request",
        response_topic: str = "engine/response",
        keepalive: int = 60,
    ):
        if mqtt is None:
            raise RuntimeError("paho-mqtt is required for MQTT support")

        self.broker_url = broker_url
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.keepalive = keepalive
        self._connected = False
        self._lock = threading.RLock()
        self._pending_requests: dict[int, Future] = {}
        self._topic_listeners: dict[str, set[Callable[[Any, str], None]]] = defaultdict(set)
        self._rpc_handlers: dict[str, Callable[[Any], Any]] = {}
        self._on_connect_callbacks: list[Callable[[], None]] = []
        self._request_id = 0

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id or f"game-engine-{uuid.uuid4().hex[:8]}",
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._connect()

    def _connect(self) -> None:
        if self.broker_url.startswith("mqtt://"):
            host = self.broker_url.replace("mqtt://", "", 1)
            port = 1883
        elif self.broker_url.startswith("tcp://"):
            host = self.broker_url.replace("tcp://", "", 1)
            port = 1883
        elif self.broker_url.startswith("ws://"):
            host = self.broker_url.replace("ws://", "", 1)
            port = 9001
        elif self.broker_url.startswith("wss://"):
            host = self.broker_url.replace("wss://", "", 1)
            port = 9001
        else:
            host = self.broker_url
            port = 1883

        if ":" in host and not host.startswith("["):
            host, port_str = host.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 1883

        self.client.connect_async(host, port, keepalive=self.keepalive)
        self.client.loop_start()

    def add_on_connect(self, callback: Callable[[], None]) -> None:
        """Run callback every time the broker connection is (re)established.

        If the client is already connected, the callback also runs immediately.
        """
        with self._lock:
            self._on_connect_callbacks.append(callback)
            already_connected = self._connected

        if already_connected:
            try:
                callback()
            except Exception as exc:
                print(f"[MQTT] on-connect callback failed: {exc}")

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] connect rc={rc}")
        self._connected = rc == 0
        if not self._connected:
            return

        self.client.subscribe(self.request_topic, qos=0)
        self.client.subscribe(self.response_topic, qos=0)

        with self._lock:
            for topic in list(self._topic_listeners):
                self.client.subscribe(topic, qos=0)
            callbacks = list(self._on_connect_callbacks)

        for callback in callbacks:
            try:
                callback()
            except Exception as exc:
                print(f"[MQTT] on-connect callback failed: {exc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] disconnected rc={rc}")
        self._connected = False

    def _on_message(self, client, userdata, message):
        payload = message.payload
        topic = message.topic

        if topic == self.response_topic:
            self._handle_rpc_response(payload)
            return

        if topic == self.request_topic:
            self._handle_jsonrpc_request(payload)
            return

        with self._lock:
            listeners = list(self._topic_listeners.items())

        for filter_topic, callbacks in listeners:
            if self._topic_matches(filter_topic, topic):
                for callback in tuple(callbacks):
                    try:
                        callback(payload, topic)
                    except Exception:
                        pass

    def _handle_jsonrpc_request(self, payload: bytes) -> None:
        try:
            request = json.loads(payload.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError):
            return

        if not isinstance(request, dict):
            return

        jsonrpc = request.get("jsonrpc")
        if jsonrpc != "2.0":
            return

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        if not isinstance(method, str):
            return

        handler = self._rpc_handlers.get(method)
        if handler is None:
            self.respond_jsonrpc(request_id, error={"code": -32601, "message": f"Method not found: {method}"})
            return

        try:
            result = handler(params)
            self.respond_jsonrpc(request_id, result=result)
        except Exception as exc:  # pragma: no cover - runtime callback failures
            self.respond_jsonrpc(request_id, error={"code": -32603, "message": str(exc)})

    def respond_jsonrpc(self, request_id: Any, result: Any = None, error: Any = None) -> None:
        if request_id is None:
            return

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
        }
        if error is not None:
            response["error"] = error
        else:
            response["result"] = result

        self.publish(self.response_topic, response)

    def register_rpc_handler(self, method: str, handler: Callable[[Any], Any]) -> None:
        with self._lock:
            self._rpc_handlers[method] = handler

    def unregister_rpc_handler(self, method: str) -> None:
        with self._lock:
            self._rpc_handlers.pop(method, None)

    def _handle_rpc_response(self, payload: bytes) -> None:
        try:
            response = json.loads(payload.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError):
            return

        if not isinstance(response, dict):
            return

        request_id = response.get("id")
        if request_id is None:
            return

        with self._lock:
            future = self._pending_requests.pop(request_id, None)

        if future is None:
            return

        if "error" in response:
            error = response["error"]
            message = error.get("message", "JSON-RPC error") if isinstance(error, dict) else str(error)
            code = error.get("code") if isinstance(error, dict) else None
            data = error.get("data") if isinstance(error, dict) else None
            future.set_exception(MqttRpcError(message, code=code, data=data))
            return

        future.set_result(response.get("result"))

    @staticmethod
    def _topic_matches(filter_topic: str, topic: str) -> bool:
        if filter_topic == topic:
            return True

        filter_parts = filter_topic.split("/")
        topic_parts = topic.split("/")

        for index, filter_part in enumerate(filter_parts):
            if filter_part == "#":
                return True
            if filter_part == "+":
                continue
            if index >= len(topic_parts):
                return False
            if filter_part != topic_parts[index]:
                return False

        return len(filter_parts) == len(topic_parts)

    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> None:
        message = self._encode_payload(payload)
        self.client.publish(topic, message, qos=qos, retain=retain)

    def publish_state(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> None:
        self.publish(topic, payload, qos=qos, retain=retain)

    def subscribe(self, topic: str, callback: Callable[[Any, str], None]) -> Callable[[], None]:
        with self._lock:
            self._topic_listeners[topic].add(callback)
            if self._connected:
                self.client.subscribe(topic, qos=0)

        def unsubscribe() -> None:
            with self._lock:
                listeners = self._topic_listeners.get(topic)
                if listeners is None:
                    return
                listeners.discard(callback)
                if not listeners:
                    self._topic_listeners.pop(topic, None)
                    if self._connected:
                        self.client.unsubscribe(topic)

        return unsubscribe

    def subscribe_state(self, topic: str, callback: Callable[[Any, str], None]) -> Callable[[], None]:
        return self.subscribe(topic, callback)

    def unsubscribe(self, topic: str, callback: Callable[[Any, str], None] | None = None) -> None:
        with self._lock:
            listeners = self._topic_listeners.get(topic)
            if listeners is None:
                return

            if callback is not None:
                listeners.discard(callback)
            else:
                listeners.clear()

            if not listeners:
                self._topic_listeners.pop(topic, None)
                if self._connected:
                    self.client.unsubscribe(topic)

    def call(self, method: str, params: Any | None = None, timeout_ms: int = 5000) -> Any:
        if not self._connected:
            raise RuntimeError("MQTT client is not connected")

        request_id = self._next_request_id()
        future = Future()
        with self._lock:
            self._pending_requests[request_id] = future

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params if params is not None else {},
            "id": request_id,
        }

        self.publish(self.request_topic, request)

        try:
            return future.result(timeout=max(timeout_ms / 1000.0, 0.1))
        except TimeoutError as exc:
            with self._lock:
                self._pending_requests.pop(request_id, None)
            raise RuntimeError(f"JSON-RPC call timed out for method '{method}'") from exc
        except MqttRpcError:
            with self._lock:
                self._pending_requests.pop(request_id, None)
            raise

    def _next_request_id(self) -> int:
        with self._lock:
            self._request_id += 1
            return self._request_id

    @staticmethod
    def _encode_payload(payload: Any) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)

        if isinstance(payload, str):
            return payload.encode("utf-8")

        if payload is None:
            return b"null"

        return json.dumps(payload).encode("utf-8")

    def stop(self) -> None:
        try:
            self.client.loop_stop()
        except Exception:
            pass

        try:
            self.client.disconnect()
        except Exception:
            pass


__all__ = [
    "AggregatedMqttClient",
    "MqttRpcError",
]

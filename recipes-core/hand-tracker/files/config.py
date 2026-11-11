#!/usr/bin/env python3

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(
    os.environ.get(
        "HAND_TRACKER_CONFIG",
        "/usr/share/hand-tracker/hand_tracker_config.json",
    )
)


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON configuration for the hand tracker."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    if not isinstance(config, dict):
        raise ValueError("Config file must contain a JSON object at the root.")

    return config


def get_recognizer_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return the recognizer section, supporting both direct and nested config layouts."""
    recognizer = config.get("recognizer", config)
    if not isinstance(recognizer, dict):
        return {}
    return recognizer


def get_config_value(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely read nested values from a config dictionary."""
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_debug_enabled(config: dict[str, Any], default: bool = False) -> bool:
    recognizer = get_recognizer_config(config)
    return bool(get_config_value(recognizer, "debug", default=default))


def get_model_path(config: dict[str, Any], default: str = "/usr/share/hand-tracker/gesture_recognizer.task") -> str:
    recognizer = get_recognizer_config(config)
    path = get_config_value(recognizer, "model", "path", default=default)
    return str(path)


def get_ipc_socket_path(config: dict[str, Any], default: str = "/tmp/hand_tracker.sock") -> str:
    recognizer = get_recognizer_config(config)
    socket_path = get_config_value(recognizer, "ipc", "socket_path", default=default)
    return str(socket_path)


def get_recognition_settings(config: dict[str, Any]) -> dict[str, float | int]:
    recognizer = get_recognizer_config(config)
    recognition = get_config_value(recognizer, "recognition", default={})
    if not isinstance(recognition, dict):
        recognition = {}

    return {
        "num_hands": int(recognition.get("num_hands", 2)),
        "min_hand_detection_confidence": float(recognition.get("min_hand_detection_confidence", 0.5)),
        "min_hand_presence_confidence": float(recognition.get("min_hand_presence_confidence", 0.5)),
        "min_tracking_confidence": float(recognition.get("min_tracking_confidence", 0.5)),
    }

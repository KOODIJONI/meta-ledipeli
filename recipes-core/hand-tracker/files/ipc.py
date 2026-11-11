#!/usr/bin/env python3

import json
import os
import socket
import time

DEFAULT_SOCKET_PATH = os.environ.get("HAND_TRACKER_IPC_SOCKET", "/tmp/hand_tracker.sock")


def build_hand_payload(current):
    """Convert the latest hand detections into a structured JSON map."""
    hands = []
    for label, gesture, coord in current:
        hands.append(
            {
                "label": label,
                "gesture": gesture,
                "wrist": {"x": coord[0], "y": coord[1]},
            }
        )

    return {
        "type": "hand_state",
        "timestamp": int(time.time() * 1000),
        "hands": hands,
    }


def send_ipc_json(payload, socket_path=DEFAULT_SOCKET_PATH):
    """Send a JSON payload to a Unix domain socket server."""
    if not payload:
        return False

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            sock.connect(socket_path)
            message = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
            sock.sendall(message)
        return True
    except (FileNotFoundError, OSError, ConnectionError):
        return False

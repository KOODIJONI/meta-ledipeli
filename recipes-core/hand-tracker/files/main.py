#!/usr/bin/env python3
import os

import cv2

from camera import close_camera, open_camera, read_frame
from config import (
    get_debug_enabled,
    get_ipc_socket_path,
    get_model_path,
    get_recognition_settings,
    load_config,
)
from inferance import analyze_frame, create_recognizer
from ipc import build_hand_payload, send_ipc_json
from parse_args import parse_args

MODEL = "/usr/share/hand-tracker/gesture_recognizer.task"


def main():
    args = parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        config = {}

    debug = args.debug or get_debug_enabled(config, default=False)
    model_path = get_model_path(config, default=MODEL)
    socket_path = get_ipc_socket_path(config, default="/tmp/hand_tracker.sock")
    recognition = get_recognition_settings(config)

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at path: {model_path}")
        print("[ERROR] Ensure the package was installed correctly via Yocto.")
        return

    cap = open_camera()
    if cap is None:
        print("[ERROR] Could not open webcam index 0. Try changing index to 1.")
        return

    last_printed = None

    with create_recognizer(
        model_path,
        num_hands=recognition["num_hands"],
        min_hand_detection_confidence=recognition["min_hand_detection_confidence"],
        min_hand_presence_confidence=recognition["min_hand_presence_confidence"],
        min_tracking_confidence=recognition["min_tracking_confidence"],
    ) as recognizer:
        if debug:
            print("[INFO] Running with config overrides. Show one or two hands to the camera. Press 'q' to quit.")
        else:
            print("[INFO] Running with default settings. Show one or two hands to the camera. Press 'q' to quit.")

        while cap.isOpened():
            frame, ok = read_frame(cap)
            if not ok:
                print("[WARNING] Camera frame failed, stopping.")
                break

            current, frame = analyze_frame(frame, recognizer)

            if current != last_printed:
                if debug:
                    if current:
                        print(" | ".join(f"{label} hand: {g} at wrist {coord}" for label, g, coord in current))
                    elif last_printed:
                        print("No hands detected")
                last_printed = current

                payload = build_hand_payload(current)
                if not send_ipc_json(payload, socket_path=socket_path):
                    print("[WARNING] Could not send IPC update. Is the socket server listening?")

    close_camera(cap)


if __name__ == "__main__":
    main()
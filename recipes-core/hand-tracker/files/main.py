#!/usr/bin/env python3
import os

import cv2

from camera import close_camera, open_camera, read_frame
from inferance import analyze_frame, create_recognizer
from ipc import build_hand_payload, send_ipc_json

MODEL = "/usr/share/hand-tracker/gesture_recognizer.task"


def main():
    if not os.path.exists(MODEL):
        print(f"[ERROR] Model file not found at static path: {MODEL}")
        print("[ERROR] Ensure the package was installed correctly via Yocto.")
        return

    cap = open_camera()
    if cap is None:
        print("[ERROR] Could not open webcam index 0. Try changing index to 1.")
        return

    last_printed = None

    with create_recognizer(MODEL) as recognizer:
        print("[INFO] Running with static model. Show one or two hands to the camera. Press 'q' to quit.")

        while cap.isOpened():
            frame, ok = read_frame(cap)
            if not ok:
                print("[WARNING] Camera frame failed, stopping.")
                break

            current, frame = analyze_frame(frame, recognizer)

            if current != last_printed:
                if current:
                    print(" | ".join(f"{label} hand: {g} at wrist {coord}" for label, g, coord in current))
                elif last_printed:
                    print("No hands detected")
                last_printed = current

                payload = build_hand_payload(current)
                if not send_ipc_json(payload):
                    print("[WARNING] Could not send IPC update. Is the socket server listening?")

    close_camera(cap)


if __name__ == "__main__":
    main()
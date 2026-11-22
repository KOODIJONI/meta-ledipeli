#!/usr/bin/env python3
"""Profiling build of hand-tracker main.py.

Same flow as main.py, but times each stage and prints a summary every
REPORT_EVERY seconds. Run it by hand with the real service stopped:

    systemctl stop hand-tracker
    python3 main_profile.py [-c /path/to/config.json]
"""
import os
import time

import cv2

from camera import close_camera, open_camera, read_frame
from config import (
    get_ipc_socket_path,
    get_model_path,
    get_recognition_settings,
    load_config,
)
from inferance import analyze_frame, create_recognizer
from ipc import build_hand_payload, send_ipc_json
from parse_args import parse_args

MODEL = "/usr/share/hand-tracker/gesture_recognizer.task"
REPORT_EVERY = 2.0  # seconds


class Stat:
    """Running avg / max in milliseconds for one stage."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.n = 0
        self.total = 0.0
        self.max = 0.0

    def add(self, seconds):
        ms = seconds * 1000.0
        self.n += 1
        self.total += ms
        if ms > self.max:
            self.max = ms

    def fmt(self):
        if self.n == 0:
            return "   -  /   -"
        return f"{self.total / self.n:5.1f}/{self.max:5.1f}"


def print_camera_info(cap):
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    code = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))
    print(
        "[CAM] "
        f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} "
        f"fps={cap.get(cv2.CAP_PROP_FPS):.1f} fourcc={code!r} "
        f"buffer={cap.get(cv2.CAP_PROP_BUFFERSIZE)}"
    )


def main():
    args = parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        config = {}

    model_path = get_model_path(config, default=MODEL)
    socket_path = get_ipc_socket_path(config, default="/tmp/hand_tracker.sock")
    recognition = get_recognition_settings(config)

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at path: {model_path}")
        return

    cap = open_camera()
    if cap is None:
        print("[ERROR] Could not open webcam.")
        return

    print_camera_info(cap)
    print(f"[CFG] recognition settings: {recognition}")
    print("[INFO] Columns are avg/max ms. 'cam fps' is what the camera really delivers,")
    print("       'loop fps' is what this process achieves. Ctrl+C to stop.\n")

    s_read, s_infer, s_send, s_total = Stat(), Stat(), Stat(), Stat()
    frames = 0
    sends = 0
    send_fail = 0
    hands_seen = 0
    last_printed = None
    window_start = time.perf_counter()

    with create_recognizer(
        model_path,
        num_hands=recognition["num_hands"],
        min_hand_detection_confidence=recognition["min_hand_detection_confidence"],
        min_hand_presence_confidence=recognition["min_hand_presence_confidence"],
        min_tracking_confidence=recognition["min_tracking_confidence"],
    ) as recognizer:
        try:
            while cap.isOpened():
                t0 = time.perf_counter()
                frame, ok = read_frame(cap)
                t1 = time.perf_counter()
                if not ok:
                    print("[WARNING] Camera frame failed, stopping.")
                    break

                current, frame = analyze_frame(frame, recognizer)
                t2 = time.perf_counter()

                if current:
                    hands_seen += 1

                if current != last_printed:
                    last_printed = current
                    payload = build_hand_payload(current)
                    ok_send = send_ipc_json(payload, socket_path=socket_path)
                    sends += 1
                    if not ok_send:
                        send_fail += 1
                    t3 = time.perf_counter()
                    s_send.add(t3 - t2)
                else:
                    t3 = t2

                s_read.add(t1 - t0)
                s_infer.add(t2 - t1)
                s_total.add(t3 - t0)
                frames += 1

                now = time.perf_counter()
                elapsed = now - window_start
                if elapsed >= REPORT_EVERY:
                    loop_fps = frames / elapsed
                    # Time spent actually waiting on the camera approximates its frame interval.
                    cam_fps = 1000.0 / (s_read.total / s_read.n) if s_read.total else 0.0
                    print(
                        f"loop fps={loop_fps:5.1f} | cam fps~{cam_fps:5.1f} | "
                        f"read {s_read.fmt()} | infer {s_infer.fmt()} | "
                        f"send {s_send.fmt()} | total {s_total.fmt()} | "
                        f"hands {hands_seen}/{frames} frames | "
                        f"sends {sends} (failed {send_fail})"
                    )
                    for s in (s_read, s_infer, s_send, s_total):
                        s.reset()
                    frames = sends = send_fail = hands_seen = 0
                    window_start = now
        except KeyboardInterrupt:
            print("\n[INFO] Stopped.")

    close_camera(cap)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Timestamps passed to recognize_for_video() must strictly increase.
_last_ts_ms = 0


def create_recognizer(
    model_path,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
):
    options = vision.GestureRecognizerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        # VIDEO mode tracks the hand between frames instead of running full
        # palm detection on every frame (IMAGE mode), which is much cheaper.
        running_mode=vision.RunningMode.VIDEO,
        num_hands=num_hands,
        min_hand_detection_confidence=min_hand_detection_confidence,
        min_hand_presence_confidence=min_hand_presence_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )
    return vision.GestureRecognizer.create_from_options(options)


def analyze_frame(frame, recognizer):
    """Run gesture recognition on a BGR frame.

    Returns (current, frame), where current is a list of
    (hand_label, gesture, (wrist_x, wrist_y)) in pixel coordinates.
    """
    global _last_ts_ms

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    _last_ts_ms = max(_last_ts_ms + 1, int(time.monotonic() * 1000))
    result = recognizer.recognize_for_video(mp_image, _last_ts_ms)

    h, w, _ = frame.shape
    current = []

    for i, lm in enumerate(result.hand_landmarks):
        hand_label = result.handedness[i][0].category_name

        if result.gestures and i < len(result.gestures) and result.gestures[i]:
            gesture = result.gestures[i][0].category_name
        else:
            gesture = "None"

        wrist = lm[0]
        current.append((hand_label, gesture, (int(wrist.x * w), int(wrist.y * h))))

    return current, frame

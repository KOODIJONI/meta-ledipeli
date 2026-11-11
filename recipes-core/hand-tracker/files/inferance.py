#!/usr/bin/env python3

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

HAND_COLORS = [(0, 255, 0), (255, 128, 0)]


def create_recognizer(model_path, num_hands=2):
    options = vision.GestureRecognizerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=num_hands,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.GestureRecognizer.create_from_options(options)


def analyze_frame(frame, recognizer):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = recognizer.recognize(mp_image)

    h, w, _ = frame.shape
    current = []

    for i, lm in enumerate(result.hand_landmarks):
        color = HAND_COLORS[i % len(HAND_COLORS)]
        hand_label = result.handedness[i][0].category_name

        if result.gestures and i < len(result.gestures) and result.gestures[i]:
            gesture = result.gestures[i][0].category_name
            score = result.gestures[i][0].score
        else:
            gesture, score = "None", 0.0

        pts = [(int(p.x * w), int(p.y * h)) for p in lm]
        wrist_x, wrist_y = pts[0]
        current.append((hand_label, gesture, (wrist_x, wrist_y)))


    return current, frame

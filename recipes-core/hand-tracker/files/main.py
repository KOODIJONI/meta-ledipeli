#!/usr/bin/env python3
import os

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Point directly to the static path where the Yocto recipe installs the model asset
MODEL = "/usr/share/hand-tracker/gesture_recognizer.task"

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

# One colour per hand so the two are easy to tell apart (BGR)
HAND_COLORS = [(0, 255, 0), (255, 128, 0)]


def main():
    if not os.path.exists(MODEL):
        print(f"[ERROR] Model file not found at static path: {MODEL}")
        print("[ERROR] Ensure the package was installed correctly via Yocto.")
        return

    cap = cv2.VideoCapture(0)
    # 640x480 gives the detector much more to work with than 320x240,
    # which matters a lot when tracking two hands.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam index 0. Try changing index to 1.")
        return

    options = vision.GestureRecognizerOptions(
        base_options=python.BaseOptions(model_asset_path=MODEL),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2,  # <-- two hands
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    last_printed = None

    with vision.GestureRecognizer.create_from_options(options) as recognizer:
        print("[INFO] Running with static model. Show one or two hands to the camera. Press 'q' to quit.")

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                print("[WARNING] Camera frame failed, stopping.")
                break

            # Mirror the frame (selfie view). MediaPipe's handedness assumes a
            # mirrored image, so "Left"/"Right" match the person's real hands.
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = recognizer.recognize(mp_image)

            h, w, _ = frame.shape
            current = []  # (hand label, gesture name) for every detected hand

            for i, lm in enumerate(result.hand_landmarks):
                color = HAND_COLORS[i % len(HAND_COLORS)]

                # Which hand is it, and what gesture is it making?
                hand_label = result.handedness[i][0].category_name  # "Left" / "Right"
                if result.gestures and i < len(result.gestures) and result.gestures[i]:
                    gesture = result.gestures[i][0].category_name
                    score = result.gestures[i][0].score
                else:
                    gesture, score = "None", 0.0
                current.append((hand_label, gesture))

                # Draw skeleton
                pts = [(int(p.x * w), int(p.y * h)) for p in lm]
                for a, b in HAND_CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], color, 2)
                for pt in pts:
                    cv2.circle(frame, pt, 3, (0, 0, 255), -1)

                # Label above the wrist/hand on the video
                x_min = min(p[0] for p in pts)
                y_min = min(p[1] for p in pts)
                text = f"{hand_label}: {gesture} ({score:.0%})"
                cv2.putText(frame, text, (max(x_min, 0), max(y_min - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            if current != last_printed:
                if current:
                    print(" | ".join(f"{label} hand: {g}" for label, g in current))
                elif last_printed:
                    print("No hands detected")
                last_printed = current

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
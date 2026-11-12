#!/usr/bin/env python3

import cv2


def open_camera(index=0, width=640, height=480):
    """Open the default webcam and configure it to the requested size."""
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        return None

    return cap


def read_frame(cap):
    """Read the next frame and mirror it for a selfie-view."""
    ok, frame = cap.read()
    if not ok:
        return None, False

    return cv2.flip(frame, 1), True


def close_camera(cap):
    """Release the camera and close OpenCV windows."""
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

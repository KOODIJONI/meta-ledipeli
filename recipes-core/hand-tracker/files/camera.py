#!/usr/bin/env python3
"""Camera access that always returns the NEWEST frame.

A background thread reads the camera continuously, so frames never queue up
in the driver while inference is busy. read_frame() blocks until a frame newer
than the previous one is available and hands back only that one; older frames
are dropped. The public API (open_camera / read_frame / close_camera, plus
isOpened/get/set on the returned object) is unchanged, so main.py and
main_profile.py work as before.
"""

import threading
import time

import cv2


class LatestFrameCamera:
    def __init__(self, cap):
        self._cap = cap
        self._cond = threading.Condition()
        self._frame = None
        self._seq = 0          # increments for every frame captured
        self._seen = 0         # last seq handed to the caller
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="camera-reader", daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.01)  # transient failure: retry instead of giving up
                continue
            with self._cond:
                self._frame = frame
                self._seq += 1
                self._cond.notify_all()

    def read(self, timeout=1.0):
        """Return (ok, frame) with the newest frame not yet returned."""
        with self._cond:
            if not self._cond.wait_for(lambda: self._seq != self._seen, timeout=timeout):
                return False, None
            self._seen = self._seq
            return True, self._frame

    def isOpened(self):
        return self._running and self._cap.isOpened()

    def get(self, prop):
        return self._cap.get(prop)

    def set(self, prop, value):
        return self._cap.set(prop, value)

    def release(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self._cap.release()


def open_camera(index=0, width=640, height=480, fps=30):
    """Open the webcam, ask for MJPG, and start the background reader."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None

    # FOURCC first, then size: some cameras only offer high FPS in MJPG.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # may be ignored by the V4L2 backend

    return LatestFrameCamera(cap)


def read_frame(cap):
    """Return (mirrored newest frame, True), or (None, False) on timeout."""
    ok, frame = cap.read()
    if not ok:
        return None, False

    return cv2.flip(frame, 1), True


def close_camera(cap):
    """Stop the reader, release the camera and close OpenCV windows."""
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

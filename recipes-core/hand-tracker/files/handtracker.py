import time
import cv2
import numpy as np

class HandTracker:
    def __init__(self, width=320, height=240):
        self.width = width
        self.height = height
        self.roi = (0, 0, width, height)
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        self.kernel = np.ones((3, 3), np.uint8)

    def process_frame(self, frame):
        # Resize if needed
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        rx, ry, rw, rh = self.roi
        sub_frame = frame[ry:ry+rh, rx:rx+rw]
        if sub_frame.size == 0:
            self.roi = (0, 0, self.width, self.height)
            return frame, 0

        hsv = cv2.cvtColor(sub_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
        mask = cv2.dilate(mask, self.kernel, iterations=1)
        mask = cv2.erode(mask, self.kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        fingers = 0
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_contour) > 400:
                hull = cv2.convexHull(max_contour, returnPoints=False)
                if len(hull) > 3:
                    defects = cv2.convexityDefects(max_contour, hull)
                    if defects is not None:
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            start = tuple(max_contour[s][0])
                            end = tuple(max_contour[e][0])
                            far = tuple(max_contour[f][0])
                            
                            a = np.linalg.norm(np.array(start) - np.array(end))
                            b = np.linalg.norm(np.array(start) - np.array(far))
                            c = np.linalg.norm(np.array(end) - np.array(far))
                            if b > 0 and c > 0:
                                angle = np.arccos((b**2 + c**2 - a**2) / (2 * b * c)) * 57.29
                                if angle <= 90:
                                    fingers += 1

                x, y, bw, bh = cv2.boundingRect(max_contour)
                cv2.rectangle(frame, (rx + x, ry + y), (rx + x + bw, ry + y + bh), (0, 255, 0), 2)
                
                pad = 35
                self.roi = (
                    max(0, rx + x - pad),
                    max(0, ry + y - pad),
                    min(self.width - max(0, rx + x - pad), bw + 2 * pad),
                    min(self.height - max(0, ry + y - pad), bh + 2 * pad)
                )
        else:
            self.roi = (0, 0, self.width, self.height)

        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 1)
        return frame, max(0, fingers)
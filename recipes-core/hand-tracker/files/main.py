import time
import cv2
import numpy as np
from handtracker import HandTracker
from socket import IPCServer

def main():
    tracker = HandTracker(320, 240)
    ipc = IPCServer()
    
    # Try opening physical camera, fallback to synthetic mode if unavailable
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    use_synthetic = not cap.isOpened()
    if use_synthetic:
        print("[INFO] Camera unavailable. Running in synthetic noise test mode.")
    else:
        print("[INFO] Camera opened successfully. Running live tracker.")

    prev = time.time()
    fps = 0.0

    try:
        while True:
            if use_synthetic:
                frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
            else:
                ok, frame = cap.read()
                if not ok:
                    break
                frame = cv2.flip(frame, 1)

            processed_frame, fingers = tracker.process_frame(frame)

            # Broadcast finger count over Unix socket
            ipc.send_data(f"FINGERS:{fingers}")

            # FPS tracking
            now = time.time()
            if prev > 0:
                fps = 0.9 * fps + 0.1 / (now - prev)
            prev = now

            if not use_synthetic:
                cv2.putText(processed_frame, f"FPS: {int(fps)}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.imshow("Hand Tracker App", processed_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01) # Throttle synthetic loop slightly

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down gracefully...")
    finally:
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        ipc.close()

if __name__ == "__main__":
    main()
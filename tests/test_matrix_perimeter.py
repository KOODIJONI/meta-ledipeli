#!/usr/bin/env python3
"""Walk a single bright pixel along the perimeter of the LED matrix."""

import argparse
import time
import sys

try:
    from recipes_core.ledmatrix_py.files.ledmatrix import LEDMatrix
except ImportError:
    try:
        from ledmatrix import LEDMatrix
    except ImportError:
        print("ERROR: could not import LEDMatrix module")
        sys.exit(1)


def perimeter_points(cols, rows):
    points = []

    # top edge: left -> right
    for x in range(cols):
        points.append((x, 0))

    # right edge: top+1 -> bottom
    for y in range(1, rows):
        points.append((cols - 1, y))

    # bottom edge: right-1 -> left
    for x in range(cols - 2, -1, -1):
        points.append((x, rows - 1))

    # left edge: bottom-1 -> top+1
    for y in range(rows - 2, 0, -1):
        points.append((0, y))

    return points


def main():
    parser = argparse.ArgumentParser(description="Move a dot around the perimeter of the LED matrix")
    parser.add_argument("--fps", type=float, default=30.0, help="Frames per second")
    parser.add_argument("--duration", type=float, default=0.0, help="Optional total runtime in seconds; 0 = infinite")
    parser.add_argument("--color", nargs=3, type=int, default=(255, 255, 255), help="RGB color")
    args = parser.parse_args()

    fps = max(1.0, args.fps)
    frame_delay = 1.0 / fps
    duration = max(0.0, args.duration)
    r, g, b = args.color

    print("Initializing LED matrix...")
    try:
        matrix = LEDMatrix()
    except Exception as exc:
        print(f"ERROR: failed to initialize matrix: {exc}")
        sys.exit(1)

    print(f"Matrix size: {matrix.rows}x{matrix.cols}")
    points = perimeter_points(matrix.cols, matrix.rows)
    start = time.time()
    step = 0

    try:
        while True:
            if duration > 0 and (time.time() - start) >= duration:
                break

            x, y = points[step % len(points)]
            matrix.fill(0, 0, 0)
            matrix.set_pixel(x, y, r, g, b)
            matrix.flush()
            step += 1
            time.sleep(frame_delay)
    except KeyboardInterrupt:
        print("\nStopping animation.")
    finally:
        matrix.fill(0, 0, 0)
        matrix.flush()
        print("Matrix cleared.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Game-loop style reproduction for the native LED matrix driver.

This script is closer to the real service flow than the basic write-only test:

- clear the matrix
- draw a few pixels as a game frame
- call get_raw_frame() to simulate the browser preview path
- call flush() to push the frame to the kernel driver

Run it directly on the Raspberry Pi that hosts the game-engine service.
"""

from __future__ import annotations

import argparse
import os
import time

try:
    from recipes_core.ledmatrix_py.files.ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover - repo layout may differ on target image
    try:
        from ledmatrix import LEDMatrix
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: could not import LEDMatrix: {exc}")
        raise SystemExit(1)


def clear_shadow(shadow: bytearray, rows: int, cols: int, r: int = 0, g: int = 0, b: int = 0) -> None:
    fill = bytes((g & 0xFF, r & 0xFF, b & 0xFF)) * (rows * cols)
    shadow[:] = fill


def draw_frame(matrix, shadow: bytearray, rows: int, cols: int, frame_index: int) -> None:
    clear_shadow(shadow, rows, cols)
    matrix.fill(0, 0, 0)

    # Game-like telemetry: a few points and a moving cursor across the matrix.
    points = [
        (0, 0),
        (cols - 1, 0),
        (0, rows - 1),
        (cols - 1, rows - 1),
        (frame_index % cols, (frame_index * 2) % rows),
        (cols // 2, rows // 2),
    ]

    for x, y in points:
        x = max(0, min(cols - 1, x))
        y = max(0, min(rows - 1, y))
        pixel = (y * cols + x) * 3
        shadow[pixel:pixel + 3] = bytes((255 & 0xFF, 0 & 0xFF, 0 & 0xFF))
        matrix.set_pixel(x, y, 0, 255, 0)

    # Toggle a red pixel to mimic a game object / pointer.
    cursor_x = frame_index % cols
    cursor_y = (frame_index * 3) % rows
    shadow[(cursor_y * cols + cursor_x) * 3:(cursor_y * cols + cursor_x) * 3 + 3] = bytes((0, 255, 255))
    matrix.set_pixel(cursor_x, cursor_y, 255, 0, 0)


def run_game_loop(iterations: int, delay_ms: int, include_raw_frame: bool) -> None:
    matrix = LEDMatrix()
    rows = matrix.rows
    cols = matrix.cols
    shadow = bytearray(rows * cols * 3)

    print(f"Matrix initialized: {rows}x{cols}")
    print(f"Looping {iterations} frames, delay={delay_ms} ms, raw_frame={include_raw_frame}")

    for idx in range(1, iterations + 1):
        try:
            draw_frame(matrix, shadow, rows, cols, idx)

            if include_raw_frame:
                blob = matrix.get_raw_frame()
                print(f"[frame {idx}] raw frame bytes={len(blob)}", flush=True)

            result = matrix.flush()
            print(f"[frame {idx}] flush={result}", flush=True)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        except Exception as exc:
            print(f"[frame {idx}] CRASHED during game-loop reproduction: {exc}", flush=True)
            raise

    print("Game-loop reproduction completed without segfault.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Replicate the game-engine LED loop on the Pi")
    parser.add_argument("--iterations", type=int, default=200, help="Number of loop iterations")
    parser.add_argument("--delay-ms", type=int, default=25, help="Sleep delay between frames in milliseconds")
    parser.add_argument("--raw-frame", action="store_true", help="Call get_raw_frame() before flush()")
    args = parser.parse_args()

    print("Starting native game-loop reproduction test...")
    print(f"Environment: {os.environ.get('HOSTNAME', 'unknown-host')}")

    try:
        run_game_loop(args.iterations, args.delay_ms, args.raw_frame)
        return 0
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

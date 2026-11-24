#!/usr/bin/env python3
"""Minimal native LED matrix reproduction for the Raspberry Pi target.

This script intentionally exercises the same native code paths used during the
runtime game loop: write pixels, clear, flush to the kernel driver, and optionally
read a raw GRB frame. It is meant to be run directly on the remote target to
confirm whether the segfault is in the native matrix driver rather than in MQTT or
Python game logic.

Example:
    python3 /usr/local/bin/test_ledmatrix_native_repro.py --iterations 100 --delay-ms 25 --raw-frame
"""

from __future__ import annotations

import argparse
import os
import sys
import time

try:
    from recipes_core.ledmatrix_py.files.ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover - repo layout may differ in the target image
    try:
        from ledmatrix import LEDMatrix
    except ImportError as exc:  # pragma: no cover - runtime-only smoke test
        print(f"ERROR: could not import LEDMatrix: {exc}")
        raise SystemExit(1)


def describe_matrix(matrix):
    print(f"Matrix initialized: {matrix.rows}x{matrix.cols}")


def exercise_matrix(matrix, iterations: int, delay_ms: int, raw_frame: bool) -> None:
    loop_count = max(1, iterations)
    delay = max(0.0, delay_ms / 1000.0)

    for idx in range(1, loop_count + 1):
        matrix.fill(0, 0, 0)

        # A few bright pixels are enough to force the driver path used by the game loop.
        coords = [
            (0, 0),
            (matrix.cols - 1, 0),
            (0, matrix.rows - 1),
            (matrix.cols - 1, matrix.rows - 1),
            (matrix.cols // 2, matrix.rows // 2),
        ]

        for x, y in coords:
            matrix.set_pixel(x, y, 255, 255, 255)

        if raw_frame:
            frame = matrix.get_raw_frame()
            print(f"[loop {idx}] raw frame length={len(frame)}", flush=True)

        result = matrix.flush()
        print(f"[loop {idx}] flush result={result}", flush=True)

        if delay > 0:
            time.sleep(delay)


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal LED matrix native reproduction test")
    parser.add_argument("--iterations", type=int, default=50, help="Number of flush cycles to run")
    parser.add_argument("--delay-ms", type=int, default=25, help="Delay between loops in milliseconds")
    parser.add_argument("--raw-frame", action="store_true", help="Call get_raw_frame() before each flush")
    args = parser.parse_args()

    print("Starting native LED matrix reproduction test...")
    print(f"Environment: {os.environ.get('HOSTNAME', 'unknown-host')}")

    try:
        matrix = LEDMatrix()
    except Exception as exc:
        print(f"ERROR: LEDMatrix() failed: {exc}")
        return 2

    try:
        describe_matrix(matrix)
        exercise_matrix(matrix, args.iterations, args.delay_ms, args.raw_frame)
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except Exception as exc:
        print(f"ERROR: unexpected exception while exercising the matrix: {exc}")
        return 3
    else:
        print("Reproduction loop completed without crashing.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

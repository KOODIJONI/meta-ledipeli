#!/usr/bin/env python3
"""Service-level reproduction for the game-engine loop.

This script mirrors the production game lifecycle more closely than the raw matrix
repro:

- create a shared LED matrix instance
- create a game-like frame buffer
- render a moving object
- simulate MQTT matrix publish if enabled
- call flush() repeatedly

It is meant to be run on the Raspberry Pi target and should help identify
whether the runtime segfault depends on the full game-loop interaction rather than
on the raw native matrix path by itself.
"""

from __future__ import annotations

import argparse
import os
import time

try:
    from recipes_core.ledmatrix_py.files.ledmatrix import LEDMatrix
except ImportError:  # pragma: no cover
    try:
        from ledmatrix import LEDMatrix
    except ImportError as exc:
        print(f"ERROR: could not import LEDMatrix: {exc}")
        raise SystemExit(1)


def build_shadow(rows: int, cols: int) -> bytearray:
    return bytearray(rows * cols * 3)


def clear_shadow(shadow: bytearray, rows: int, cols: int) -> None:
    shadow[:] = bytes((0, 0, 0)) * (rows * cols)


def set_shadow_pixel(shadow: bytearray, cols: int, x: int, y: int, r: int, g: int, b: int) -> None:
    px = (y * cols + x) * 3
    shadow[px:px + 3] = bytes((g & 0xFF, r & 0xFF, b & 0xFF))


def render_frame(matrix: LEDMatrix, shadow: bytearray, rows: int, cols: int, frame_index: int) -> None:
    clear_shadow(shadow, rows, cols)
    matrix.fill(0, 0, 0)

    # Game-like frame with a moving cursor and a few static points.
    points = [
        (0, 0),
        (cols - 1, 0),
        (0, rows - 1),
        (cols - 1, rows - 1),
        (cols // 2, rows // 2),
    ]

    for x, y in points:
        x = max(0, min(cols - 1, x))
        y = max(0, min(rows - 1, y))
        set_shadow_pixel(shadow, cols, x, y, 255, 255, 255)
        matrix.set_pixel(x, y, 255, 255, 255)

    cursor_x = frame_index % cols
    cursor_y = (frame_index * 3) % rows
    set_shadow_pixel(shadow, cols, cursor_x, cursor_y, 255, 0, 0)
    matrix.set_pixel(cursor_x, cursor_y, 255, 0, 0)

    # Simulate the browser preview path by extracting a raw GRB byte blob.
    blob = matrix.get_raw_frame()
    if len(blob) != rows * cols * 3:
        print(f"Unexpected blob length: {len(blob)} != {rows * cols * 3}")
    return blob


def run_repro(iterations: int, delay_ms: int, simulate_publish: bool) -> None:
    matrix = LEDMatrix()
    rows = matrix.rows
    cols = matrix.cols
    shadow = build_shadow(rows, cols)

    print(f"Matrix initialized: {rows}x{cols}")
    print(f"Running {iterations} iterations, delay={delay_ms} ms, simulate_publish={simulate_publish}")

    for idx in range(1, iterations + 1):
        try:
            blob = render_frame(matrix, shadow, rows, cols, idx)
            if simulate_publish:
                # Mimic the MQTT publish payload used by the browser simulator.
                payload = bytes(blob)
                print(f"[frame {idx}] payload_bytes={len(payload)}", flush=True)
            result = matrix.flush()
            print(f"[frame {idx}] flush={result}", flush=True)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        except Exception as exc:
            print(f"[frame {idx}] CRASHED in game-engine reproduction: {exc}", flush=True)
            raise

    print("Service-style game-loop reproduction completed without segfault.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Service-style game loop reproduction on the Pi")
    parser.add_argument("--iterations", type=int, default=200, help="Number of frames to render")
    parser.add_argument("--delay-ms", type=int, default=25, help="Sleep between frames in milliseconds")
    parser.add_argument("--simulate-publish", action="store_true", help="Approximate the MQTT matrix publish path")
    args = parser.parse_args()

    print("Starting service-style game-loop reproduction...")
    print(f"Environment: {os.environ.get('HOSTNAME', 'unknown-host')}")

    try:
        run_repro(args.iterations, args.delay_ms, args.simulate_publish)
        return 0
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

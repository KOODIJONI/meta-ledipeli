#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${1:-/usr/local/bin/test_ledmatrix_native_repro.py}"
ITERATIONS="${2:-50}"
DELAY_MS="${3:-25}"
RAW_FRAME_FLAG=""

if [ "${4:-}" = "--raw-frame" ]; then
  RAW_FRAME_FLAG="--raw-frame"
fi

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Missing reproduction script: $SCRIPT_PATH"
  exit 1
fi

python3 "$SCRIPT_PATH" --iterations "$ITERATIONS" --delay-ms "$DELAY_MS" $RAW_FRAME_FLAG

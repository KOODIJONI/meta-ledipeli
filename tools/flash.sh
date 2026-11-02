#!/bin/bash
set -e

# Configuration
TARGET_IP="${1:-192.168.1.108}"
TARGET_USER="${TARGET_USER:-root}"
TARGET_DISK="${TARGET_DISK:-/dev/mmcblk0}"

# Locate deploy images directory relative to meta-ledipeli/tools/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR/../../build/tmp/deploy/images/raspberrypi3"

if [ ! -d "$DEPLOY_DIR" ]; then
    # Fallback search path
    DEPLOY_DIR="../build/tmp/deploy/images/raspberrypi3"
fi

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "[ERROR] Yocto deploy directory not found at: $DEPLOY_DIR"
    exit 1
fi

# Look for .rootfs.wic or newest valid .wic image
WIC_IMAGE=$(ls -t "$DEPLOY_DIR"/*.rootfs.wic "$DEPLOY_DIR"/*.wic 2>/dev/null | grep -v "\.symlink$" | head -n 1)

if [ -z "$WIC_IMAGE" ] || [ ! -f "$WIC_IMAGE" ]; then
    echo "[ERROR] No valid .wic image found in $DEPLOY_DIR"
    exit 1
fi

# Resolve symlink if it points to a timestamped image file
REAL_IMAGE=$(readlink -f "$WIC_IMAGE")

echo "[INFO] Selected image: $(basename "$WIC_IMAGE") -> $(basename "$REAL_IMAGE")"
echo "[INFO] Target: $TARGET_USER@$TARGET_IP ($TARGET_DISK)"
read -p "Proceed with flashing? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Flashing aborted."
    exit 0
fi

echo "[INFO] Streaming image to target..."
ssh "$TARGET_USER@$TARGET_IP" "dd of=$TARGET_DISK bs=4M" < "$REAL_IMAGE"
echo "[INFO] Flash completed successfully!"

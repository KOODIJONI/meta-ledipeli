#!/usr/bin/env bash
set -e

# Ensure script is run as root (needed for raw block device writing)
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this script with sudo: sudo $0"
  exit 1
fi

# Define the default Yocto deploy path
DEFAULT_DIR="../build/tmp/deploy/images/raspberrypi3"
# Determine the WIC archive or image path
if [ -n "$1" ]; then
  WIC_TARGET="$1"
else
  # Search for compressed or raw WIC images in the default deploy directory or current directory
  if [ -d "$DEFAULT_DIR" ]; then
    WIC_TARGET=$(find "$DEFAULT_DIR" -maxdepth 1 -name "ledipeli-image-raspberrypi3*.wic*" ! -name "*.bmap" | head -n 1)
  fi
  
  if [ -z "$WIC_TARGET" ] || [ ! -f "$WIC_TARGET" ]; then
    WIC_TARGET=$(find . -maxdepth 1 -name "ledipeli-image-raspberrypi3*.wic*" ! -name "*.bmap" | head -n 1)
  fi
  
  if [ -z "$WIC_TARGET" ]; then
    echo "[-] Error: No WIC image or archive found in '$DEFAULT_DIR' or current directory."
    echo "[!] Usage: sudo $0 [path-to-image.wic.bz2]"
    exit 1
  fi
  echo "[+] Auto-detected image target: $WIC_TARGET"
fi

# Handle decompression if the file is a bz2 archive
WIC_IMAGE="${WIC_TARGET%.bz2}"
if [[ "$WIC_TARGET" == *.bz2 ]]; then
  if [ ! -f "$WIC_IMAGE" ]; then
    echo "[+] Decompressing bz2 archive (handling hard links safely)..."
    bzcat "$WIC_TARGET" > "$WIC_IMAGE"
  else
    echo "[+] Uncompressed raw .wic image already exists."
  fi
else
  WIC_IMAGE="$WIC_TARGET"
fi

if [ ! -f "$WIC_IMAGE" ]; then
  echo "[-] Error: Resolved WIC image '$WIC_IMAGE' not found."
  exit 1
fi

echo ""
echo "=== Available Disks ==="
lsblk -d -o NAME,SIZE,RM,MODEL | grep -E "NAME|disk"
echo "======================="

read -p "[?] Enter the target SD card drive name (e.g., sdb): " TARGET_DISK

# Basic safety validation
if [ -z "$TARGET_DISK" ] || [ ! -e "/dev/$TARGET_DISK" ]; then
  echo "[-] Invalid drive specified. Aborting."
  exit 1
fi

TARGET_PATH="/dev/$TARGET_DISK"

# Prevent writing to common system drives
if [ "$TARGET_PATH" = "/dev/sda" ] || [ "$TARGET_PATH" = "/dev/nvme0n1" ]; then
  echo "[!] FATAL: You selected $TARGET_PATH, which looks like a main system drive! Aborting for safety."
  exit 1
fi

echo ""
echo "[!] WARNING: This will DESTROY all data on $TARGET_PATH!"
lsblk "$TARGET_PATH"
echo ""
read -p "Are you sure you want to continue? (y/N): " CONFIRM

if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "[+] Unmounting partitions on $TARGET_PATH..."
  umount ${TARGET_PATH}* 2>/dev/null || true

  echo "[+] Flashing $WIC_IMAGE to $TARGET_PATH..."
  dd if="$WIC_IMAGE" of="$TARGET_PATH" bs=4M status=progress conv=fsync

  sync
  echo "[+] Flashing complete! You can safely remove the SD card."
else
  echo "[-] Operation cancelled."
  exit 0
fi

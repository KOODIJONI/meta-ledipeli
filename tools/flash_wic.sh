#!/usr/bin/env bash
set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this script with sudo or as root."
  exit 1
fi

# Define the default Yocto deploy path based on your environment
DEFAULT_DIR="../build/tmp/deploy/images/raspberrypi3"

# Determine the WIC image path
if [ -n "$1" ]; then
  WIC_IMAGE="$1"
else
  # Search for the ledipeli wic image in the default deploy directory or current directory
  if [ -d "$DEFAULT_DIR" ]; then
    WIC_IMAGE=$(find "$DEFAULT_DIR" -maxdepth 1 -name "ledipeli-image-raspberrypi3*.wic" | head -n 1)
  fi
  
  if [ -z "$WIC_IMAGE" ] || [ ! -f "$WIC_IMAGE" ]; then
    # Fallback to current directory
    WIC_IMAGE=$(find . -maxdepth 1 -name "ledipeli-image-raspberrypi3*.wic" | head -n 1)
  fi
  
  if [ -z "$WIC_IMAGE" ]; then
    echo "[-] Error: No WIC image found in '$DEFAULT_DIR' or current directory."
    echo "[!] Usage: sudo $0 [path-to-image.wic]"
    exit 1
  fi
  echo "[+] Auto-detected WIC image: $WIC_IMAGE"
fi

if [ ! -f "$WIC_IMAGE" ]; then
  echo "[-] Error: Image file '$WIC_IMAGE' not found."
  exit 1
fi

echo "=== Available Disks ==="
lsblk -d -o NAME,SIZE,RM,MODEL | grep -E "NAME|disk"
echo "======================="

read -p "[?] Enter the target USB drive name (e.g., sdb): " TARGET_DISK

# Basic safety validation
if [ -z "$TARGET_DISK" ] || [ ! -e "/dev/$TARGET_DISK" ]; then
  echo "[-] Invalid drive specified. Aborting."
  exit 1
fi

TARGET_PATH="/dev/$TARGET_DISK"

# Prevent writing to the main system drive
if [ "$TARGET_PATH" = "/dev/sda" ]; then
  echo "[!] FATAL: You selected /dev/sda, which is your main system drive! Aborting for safety."
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
  echo "[+] Flashing complete! You can safely remove the USB drive."
else
  echo "[-] Operation cancelled."
  exit 0
fi

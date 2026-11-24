#!/usr/bin/env bash
set -Eeuo pipefail

OVERLAY="ledipeli-spi-ws281x-test"
HOST="${1:?Usage: $0 HOST SOURCE.dts}"
SOURCE="${2:?Usage: $0 HOST SOURCE.dts}"
TARGET="root@${HOST}"

for cmd in dtc ssh scp; do
    command -v "$cmd" >/dev/null || {
        echo "ERROR: Missing command: $cmd"
        exit 1
    }
done

[[ -f "$SOURCE" ]] || {
    echo "ERROR: Source DTS not found: $SOURCE"
    exit 1
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

DTBO="$TMP/$OVERLAY.dtbo"
CHECK="$TMP/check.dts"

echo "[1/5] Compiling DTS..."

dtc -@ -I dts -O dtb -o "$DTBO" "$SOURCE"

echo "[2/5] Verifying compiled overlay..."

dtc -I dtb -O dts -o "$CHECK" "$DTBO"

for required in \
    'spi@54000' \
    'spi@64000' \
    'ledmatrix_spi1_pins' \
    'ledmatrix_spi5_pins' \
    'pinctrl-0' \
    'rp1_gpio'; do
    if ! grep -Fq "$required" "$CHECK"; then
        echo "ERROR: Missing from compiled overlay: $required"
        exit 1
    fi
done

echo "Overlay verification passed."

echo "[3/5] Copying overlay..."

scp "$DTBO" "$TARGET:/tmp/$OVERLAY.dtbo"

echo "[4/5] Installing on Raspberry Pi..."

ssh "$TARGET" sh -s -- "$OVERLAY" <<'REMOTE'
set -eu

NAME="$1"

if [ -d /boot/firmware/overlays ]; then
    DIR=/boot/firmware/overlays
    CONFIG=/boot/firmware/config.txt
else
    DIR=/boot/overlays
    CONFIG=/boot/config.txt
fi

STAMP="$(date +%Y%m%d-%H%M%S)"

cp -a "$CONFIG" "$CONFIG.backup-$STAMP"

if [ -f "$DIR/$NAME.dtbo" ]; then
    cp -a "$DIR/$NAME.dtbo" "$DIR/$NAME.dtbo.backup-$STAMP"
fi

cp "/tmp/$NAME.dtbo" "$DIR/$NAME.dtbo"
chmod 0644 "$DIR/$NAME.dtbo"
rm -f "/tmp/$NAME.dtbo"

TMP_CONFIG="$CONFIG.tmp"

awk '
    !/^dtoverlay=ledipeli-spi-ws281x(-test)?([,[:space:]]|$)/
' "$CONFIG" > "$TMP_CONFIG"

printf '\n# LED matrix test overlay\n' >> "$TMP_CONFIG"
printf 'dtoverlay=%s\n' "$NAME" >> "$TMP_CONFIG"

mv "$TMP_CONFIG" "$CONFIG"

echo "Installed: $DIR/$NAME.dtbo"
echo "Configuration: $CONFIG"
grep -n 'ledipeli-spi-ws281x' "$CONFIG"
REMOTE

echo "[5/5] Installation complete."

read -r -p "Reboot Raspberry Pi now? [y/N] " ANSWER

if [[ "$ANSWER" =~ ^[Yy]$ ]]; then
    ssh "$TARGET" reboot || true
    echo "Reboot requested."
else
    echo "Reboot skipped."
fi

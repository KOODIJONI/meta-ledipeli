
#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./test-ledmatrix-overlay.sh PI_IP [SOURCE_DTS]

PI_IP="${1:?Usage: $0 PI_IP [SOURCE_DTS]}"
SSH_USER="root"
SSH_TARGET="${SSH_USER}@${PI_IP}"

SOURCE_DTS="${2:-meta-ledipeli/recipes-kernel/ledmatrix-dt/files/overlays/ledipeli-spi-ws281x.dts}"

TEST_NAME="ledipeli-spi-ws281x-test"
ORIGINAL_NAME="ledipeli-spi-ws281x"
REMOTE_DIR="/boot/overlays"

for cmd in dtc python3 ssh scp; do
    command -v "$cmd" >/dev/null || {
        echo "ERROR: Missing command: $cmd"
        exit 1
    }
done

[[ -f "$SOURCE_DTS" ]] || {
    echo "ERROR: DTS not found: $SOURCE_DTS"
    exit 1
}

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

TEST_DTS="$WORK_DIR/${TEST_NAME}.dts"
TEST_DTBO="$WORK_DIR/${TEST_NAME}.dtbo"

echo "[1/5] Creating test DTS..."

python3 - "$SOURCE_DTS" "$TEST_DTS" <<'PY'
import re
import sys

src, dst = sys.argv[1:3]

with open(src) as f:
    lines = f.readlines()

result = []
skip = False
depth = 0
removed_spi3 = False
removed_pinctrl = 0

for line in lines:
    if not skip and re.match(r'^\s*fragment@3\s*\{', line):
        skip = True
        removed_spi3 = True
        depth = line.count('{') - line.count('}')
        if depth == 0:
            skip = False
        continue

    if skip:
        depth += line.count('{') - line.count('}')
        if depth <= 0:
            skip = False
        continue

    if re.match(r'^\s*speed3\s*=', line):
        continue

    result.append(line)

if not removed_spi3:
    sys.exit("ERROR: fragment@3 not found; refusing to modify DTS")

if removed_pinctrl == 0:
    print("WARNING: No pinctrl references found")

with open(dst, "w") as f:
    f.writelines(result)

print(f"Removed SPI3 fragment and {removed_pinctrl} pinctrl properties")
PY

echo "[2/5] Compiling test overlay..."

dtc -@ -I dts -O dtb -o "$TEST_DTBO" "$TEST_DTS"

echo "[3/5] Copying overlay to Raspberry Pi..."

scp "$TEST_DTBO" "${SSH_TARGET}:/tmp/${TEST_NAME}.dtbo"

echo "[4/5] Backing up and configuring Raspberry Pi..."

ssh "$SSH_TARGET" sh -s -- "$TEST_NAME" "$ORIGINAL_NAME" <<'REMOTE'
set -eu

TEST_NAME="$1"
ORIGINAL_NAME="$2"
STAMP="$(date +%Y%m%d-%H%M%S)"

CONFIG="/boot/config.txt"
OVERLAYS="/boot/overlays"

[ -f "$CONFIG" ] || {
    echo "ERROR: $CONFIG not found"
    exit 1
}

[ -f "$OVERLAYS/$ORIGINAL_NAME.dtbo" ] || {
    echo "ERROR: Original overlay not found"
    exit 1
}

grep -Eq "^dtoverlay=${ORIGINAL_NAME}([,[:space:]]|$)" "$CONFIG" || {
    echo "ERROR: Original overlay entry not found in $CONFIG"
    exit 1
}

cp -p "$CONFIG" "$CONFIG.backup-$STAMP"
cp -p "$OVERLAYS/$ORIGINAL_NAME.dtbo" \
      "$OVERLAYS/$ORIGINAL_NAME.dtbo.backup-$STAMP"

cp "/tmp/$TEST_NAME.dtbo" "$OVERLAYS/$TEST_NAME.dtbo"
chmod 0644 "$OVERLAYS/$TEST_NAME.dtbo"

sed -i \
    "s|^dtoverlay=$ORIGINAL_NAME,|dtoverlay=$TEST_NAME,|" \
    "$CONFIG"

echo "Backups created with suffix: $STAMP"
echo "New overlay configuration:"
grep "^dtoverlay=$TEST_NAME" "$CONFIG"

sync
REMOTE

echo "[5/5] Test overlay installed."

read -r -p "Reboot Raspberry Pi now? [y/N] " ANSWER

if [[ "$ANSWER" =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    ssh "$SSH_TARGET" "reboot" || true
else
    echo "Not rebooted. The test overlay is installed but won't be applied until reboot."
fi

echo "Done."


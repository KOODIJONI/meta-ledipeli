FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " file://overlays/ledipeli-spi-ws281x.dts"

KERNEL_DEVICETREE:append = " overlays/ledipeli-spi-ws281x.dtbo"

do_configure:append() {
    install -d ${S}/arch/arm/boot/dts/overlays

    install -m 0644 \
        ${WORKDIR}/overlays/ledipeli-spi-ws281x.dts \
        ${S}/arch/arm/boot/dts/overlays/ledipeli-spi-ws281x-overlay.dts

    OVERLAY_MAKEFILE="${S}/arch/arm/boot/dts/overlays/Makefile"

    if ! grep -q "ledipeli-spi-ws281x.dtbo" "$OVERLAY_MAKEFILE"; then
        echo "dtbo-y += ledipeli-spi-ws281x.dtbo" >> "$OVERLAY_MAKEFILE"
    fi
}

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " file://overlays/ledipeli-spi-ws281x.dts"

KERNEL_DEVICETREE:append = " overlays/ledipeli-spi-ws281x.dtbo"

do_configure:append() {
    if [ -f "${WORKDIR}/overlays/ledipeli-spi-ws281x.dts" ]; then
        cp ${WORKDIR}/overlays/ledipeli-spi-ws281x.dts \
         ${S}/arch/arm/boot/dts/overlays/ledipeli-spi-ws281x-overlay.dts
    fi

    OVERLAY_MAKEFILE="${S}/arch/arm/boot/dts/overlays/Makefile"
    if [ -f "$OVERLAY_MAKEFILE" ] && ! grep -q "ledipeli-spi-ws281x.dtbo" "$OVERLAY_MAKEFILE"; then
        echo "dtbo-y += ledipeli-spi-ws281x.dtbo" >> "$OVERLAY_MAKEFILE"
    fi
}

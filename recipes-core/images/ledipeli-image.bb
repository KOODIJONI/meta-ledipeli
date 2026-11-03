SUMMARY = "Custom LED Strip Controller Image for Raspberry Pi 3"
LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL:append = " \
    packagegroup-core-boot \
    dropbear \
    nginx \
    python3 \
    python3-pip \
    python3-core \
    python3-modules \
    opencv \
    python3-opencv \
    libv4l \
    v4l-utils \
    hand-tracker \
    systemd-conf \
    libtensorflow-lite \
    python3-tensorflow-lite \
"
SYSTEMD_AUTO_ENABLE:dropbear = "enable"
IMAGE_ROOTFS_SIZE ?= "819200"

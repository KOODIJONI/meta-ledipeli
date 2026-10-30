SUMMARY = "Custom LED Strip Controller Image for Raspberry Pi 3"
LICENSE = "MIT"

inherit core-image

INIT_MANAGER = "systemd"


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
"

# Set a reasonable rootfs size (in KB)
IMAGE_ROOTFS_SIZE ?= "819200"

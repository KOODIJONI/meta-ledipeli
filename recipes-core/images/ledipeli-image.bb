SUMMARY = "Custom LED Strip Controller Image for Raspberry Pi 3"
LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL:append = " \
    mosquitto \
    mosquitto-clients \
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
    mesa \
    mesa-megadriver \
    libegl-mesa \
    libgles2-mesa \
    python3-mediapipe \
    hand-client \
"
SYSTEMD_AUTO_ENABLE:dropbear = "enable"
IMAGE_ROOTFS_SIZE ?= "819200"

PACKAGECONFIG:append:pn-mosquitto = " websockets"
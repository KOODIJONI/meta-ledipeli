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
    ledmatrix-kernel \
    ledmatrix-driver \
    ledmatrix-py \
    game-engine \
"
ENABLE_SPI_BUS = "1"

RPI_EXTRA_CONFIG:append = "\n\
dtoverlay=spi0-1cs,cs0_spidev=off\n\
dtoverlay=spi1-1cs,cs0_spidev=off\n\
dtoverlay=spi2-1cs-pi5,cs0_spidev=off\n\
dtoverlay=spi3-1cs-pi5,cs0_spidev=off\n\
dtoverlay=ledipeli-spi-ws281x,speed0=6400000,speed1=6400000,speed2=6400000,speed3=6400000\n\
"

RPI_EXTRA_IMAGE_BOOT_FILES:append = " \
    ledipeli-spi-ws281x.dtbo;overlays/ledipeli-spi-ws281x.dtbo \
"

RPI_EXTRA_CONFIG:append = "\n\
dtoverlay=ledipeli-spi-ws281x,speed0=6400000,speed1=6400000,speed2=6400000,speed3=6400000\n\
"

SYSTEMD_AUTO_ENABLE:dropbear = "enable"
IMAGE_ROOTFS_SIZE ?= "819200"

PACKAGECONFIG:append:pn-mosquitto = " websockets"
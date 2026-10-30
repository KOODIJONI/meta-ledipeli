SUMMARY = "Custom LED Strip Controller Image for Raspberry Pi 3"
LICENSE = "MIT"

inherit core-image

# Include basic boot packages and Dropbear SSH for headless access
IMAGE_INSTALL += " \
    packagegroup-core-boot \
    dropbear \
"

# Set a reasonable rootfs size (in KB)
IMAGE_ROOTFS_SIZE ?= "819200"

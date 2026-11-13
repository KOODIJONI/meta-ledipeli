
SUMMARY = "LED Matrix Kernel Buffer Receiver Driver"
DESCRIPTION = "Four-channel asynchronous SPI LED matrix driver"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=d41d8cd98f00b204e9800998ecf8427e"

inherit module
do_configure[noexec] = "1"
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://src/ledmatrix.c \
    file://include/ledmatrix.h \
    file://Makefile \
    file://COPYING \
"

S = "${WORKDIR}"

KERNEL_MODULE_AUTOLOAD += "ledmatrix"

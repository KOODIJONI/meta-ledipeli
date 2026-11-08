SUMMARY = "LED Matrix Kernel Buffer Receiver Driver"
DESCRIPTION = "Creates /dev/ledmatrix to receive PWM buffers from user-space."
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=d41d8cd98f00b204e9800998ecf8427e"

inherit module

SRC_URI = "file://src/ledmatrix.c \
           file://include/ledmatrix.h \
           file://Makefile \
           file://COPYING"

S = "${WORKDIR}"

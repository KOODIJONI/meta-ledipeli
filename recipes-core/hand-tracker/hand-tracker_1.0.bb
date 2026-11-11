SUMMARY = "Python-based Hand Tracker with MediaPipe and OpenCV"
DESCRIPTION = "Captures camera frames, runs MediaPipe gesture recognition, and detects hand landmarks."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://main.py \
           file://gesture_recognizer.task \
           "

S = "${WORKDIR}"

# Switch from cmake to setuptools3 or a simple script deployment
inherit systemd

RDEPENDS:${PN} += "\
    python3-core \
    python3-opencv \
    python3-mediapipe \
    python3-numpy \
"

SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {
    # 1. Install Python script as an executable in /usr/bin
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/main.py ${D}${bindir}/hand-tracker

    # 2. Install Model Asset
    install -d ${D}${datadir}/hand-tracker
    install -m 0644 ${WORKDIR}/gesture_recognizer.task ${D}${datadir}/hand-tracker/

}

FILES:${PN} += "\
    ${bindir}/hand-tracker \
    ${datadir}/hand-tracker/*.task \
"

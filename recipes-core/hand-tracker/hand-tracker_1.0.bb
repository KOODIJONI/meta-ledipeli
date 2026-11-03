SUMMARY = "Modular C++ Hand Tracker with OpenCV, TFLite, and Unix Socket IPC"
DESCRIPTION = "Captures camera frames, runs TFLite hand landmark inference, and streams coordinates via Unix sockets."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://main.cpp \
           file://camera.hpp \
           file://camera.cpp \
           file://inference.hpp \
           file://inference.cpp \
           file://ipc.hpp \
           file://ipc.cpp \
           file://CMakeLists.txt \
           file://hand-tracker.service \
           file://hand_landmark_lite.tflite"

S = "${WORKDIR}"

inherit cmake systemd

DEPENDS = "opencv libtensorflow-lite pkgconfig-native flatbuffers"
RDEPENDS:${PN} = "opencv libtensorflow-lite flatbuffers"

SYSTEMD_SERVICE:${PN} = "hand-tracker.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_configure:prepend() {
    if [ -f ${STAGING_LIBDIR}/pkgconfig/libtensorflow-lite.pc ] && [ ! -f ${STAGING_LIBDIR}/pkgconfig/tensorflow-lite.pc ]; then
        ln -s libtensorflow-lite.pc ${STAGING_LIBDIR}/pkgconfig/tensorflow-lite.pc
    fi
}

do_install() {
    # 1. Install compiled binary
    install -d ${D}${bindir}
    install -m 0755 hand-tracker ${D}${bindir}/

    # 2. Install TFLite model asset
    install -d ${D}${datadir}/hand-tracker
    install -m 0644 ${WORKDIR}/hand_landmark_lite.tflite ${D}${datadir}/hand-tracker/

    # 3. Install systemd service unit
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/hand-tracker.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} += "${datadir}/hand-tracker/hand_landmark_lite.tflite"
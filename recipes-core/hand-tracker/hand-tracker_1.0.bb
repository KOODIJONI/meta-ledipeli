SUMMARY = "Python-based Hand Tracker with MediaPipe and OpenCV"
DESCRIPTION = "Captures camera frames, runs MediaPipe gesture recognition, and detects hand landmarks."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://main.py \
           file://camera.py \
           file://config.py \
           file://inferance.py \
           file://ipc.py \
           file://parse_args.py \
           file://hand_tracker.service \
           file://hand_tracker_config.json \
           file://gesture_recognizer.task \
           "

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} += "\
    python3-core \
    python3-opencv \
    python3-mediapipe \
    python3-numpy \
"

SYSTEMD_AUTO_ENABLE:${PN} = "enable"
SYSTEMD_SERVICE:${PN} = "hand-tracker.service"

do_configure[noexec] = "1"
do_compile[noexec] = "1"

do_install() {
    install -d ${D}${bindir}
    install -d ${D}${datadir}/hand-tracker
    install -d ${D}${systemd_unitdir}/system

    install -m 0755 ${WORKDIR}/main.py ${D}${datadir}/hand-tracker/main.py
    install -m 0755 ${WORKDIR}/camera.py ${D}${datadir}/hand-tracker/camera.py
    install -m 0755 ${WORKDIR}/config.py ${D}${datadir}/hand-tracker/config.py
    install -m 0755 ${WORKDIR}/inferance.py ${D}${datadir}/hand-tracker/inferance.py
    install -m 0755 ${WORKDIR}/ipc.py ${D}${datadir}/hand-tracker/ipc.py
    install -m 0755 ${WORKDIR}/parse_args.py ${D}${datadir}/hand-tracker/parse_args.py
    install -m 0644 ${WORKDIR}/hand_tracker_config.json ${D}${datadir}/hand-tracker/hand_tracker_config.json
    install -m 0644 ${WORKDIR}/gesture_recognizer.task ${D}${datadir}/hand-tracker/gesture_recognizer.task

    cat > ${D}${bindir}/hand-tracker <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/share/hand-tracker/main.py "$@"
EOF
    chmod 0755 ${D}${bindir}/hand-tracker

    install -m 0644 ${WORKDIR}/hand_tracker.service ${D}${systemd_unitdir}/system/hand-tracker.service
}

FILES:${PN} += "\
    ${bindir}/hand-tracker \
    ${datadir}/hand-tracker \
    ${systemd_unitdir}/system/hand-tracker.service \
"

SUMMARY = "High-performance ROI Hand Tracker & IPC Service"
DESCRIPTION = "OpenCV-based hand tracking application with Unix socket IPC and systemd integration"
LICENSE = "CLOSED"

SRC_URI = " \
    file://handtracker.py \
    file://main.py \
    file://socket.py \
    file://hand_tracker.service \
"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "hand_tracker.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = " \
    python3 \
    python3-opencv \
    python3-numpy \
"

do_install() {
    # Install application source files to /opt/hand_tracker/
    install -d ${D}/opt/hand_tracker/
    install -m 0644 ${WORKDIR}/handtracker.py ${D}/opt/hand_tracker/
    install -m 0755 ${WORKDIR}/main.py ${D}/opt/hand_tracker/
    install -m 0644 ${WORKDIR}/socket.py ${D}/opt/hand_tracker/

    # Install systemd service file
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/hand_tracker.service ${D}${systemd_system_unitdir}/
}

FILES:${PN} = " \
    /opt/hand_tracker/* \
    ${systemd_system_unitdir}/hand_tracker.service \
"
SUMMARY = "Game engine for matrix-based hand-tracking games"
DESCRIPTION = "Python game engine with Tetris and matrix test game support"
LICENSE = "CLOSED"

inherit systemd

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://main.py \
    file://config.py \
    file://parse_arg.py \
    file://games \
    file://config/game_engine.json \
    file://game-engine.service \
"

S = "${WORKDIR}"

SYSTEMD_SERVICE:${PN} = "game-engine.service"

RDEPENDS:${PN} += "python3"

FILES:${PN} += "${bindir}/game-engine ${sysconfdir}/game-engine ${systemd_unitdir}/system/game-engine.service"


do_install() {
    install -d ${D}${bindir}/game-engine
    install -m 0755 ${WORKDIR}/main.py ${D}${bindir}/game-engine/main.py
    install -m 0644 ${WORKDIR}/config.py ${D}${bindir}/game-engine/config.py
    install -m 0644 ${WORKDIR}/parse_arg.py ${D}${bindir}/game-engine/parse_arg.py

    cp -r ${WORKDIR}/games ${D}${bindir}/game-engine/

    install -d ${D}${sysconfdir}/game-engine
    install -m 0644 ${WORKDIR}/config/game_engine.json ${D}${sysconfdir}/game-engine/game_engine.json

    install -d ${D}${systemd_unitdir}/system
    install -m 0644 ${WORKDIR}/game-engine.service ${D}${systemd_unitdir}/system/game-engine.service
}

SUMMARY = "Game engine for matrix-based hand-tracking games"
DESCRIPTION = "Python game engine with Tetris and matrix test game support"
LICENSE = "CLOSED"

inherit systemd

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI = " \
    file://main.py \
    file://game_manager.py \
    file://mqtt_client.py \
    file://config.py \
    file://parse_arg.py \
    file://games \
    file://config/game_engine.json \
    file://game-engine.service \
    file://base_game \
    file://assets \
"

S = "${WORKDIR}"

SYSTEMD_SERVICE:${PN} = "game-engine.service"

RDEPENDS:${PN} += "python3"

FILES:${PN} += "${bindir}/game-engine ${sysconfdir}/game-engine ${systemd_unitdir}/system/game-engine.service"


do_install() {
    install -d ${D}${bindir}/game-engine
    install -m 0755 ${WORKDIR}/main.py ${D}${bindir}/game-engine/main.py
    install -m 0755 ${WORKDIR}/game_manager.py ${D}${bindir}/game-engine/game_manager.py
    install -m 0644 ${WORKDIR}/mqtt_client.py ${D}${bindir}/game-engine/mqtt_client.py
    install -m 0644 ${WORKDIR}/config.py ${D}${bindir}/game-engine/config.py
    install -m 0644 ${WORKDIR}/parse_arg.py ${D}${bindir}/game-engine/parse_arg.py

    cp -r ${WORKDIR}/games ${D}${bindir}/game-engine/
    cp -r ${WORKDIR}/base_game ${D}${bindir}/game-engine/

    # Create assets directory and selectively install screensaver 0 through 10
    install -d ${D}${bindir}/game-engine/assets
    for i in $(seq 0 10); do
        if [ -f "${WORKDIR}/assets/screensaver_${i}.bin" ]; then
            install -m 0644 ${WORKDIR}/assets/screensaver_${i}.bin ${D}${bindir}/game-engine/assets/
        fi
    done

    install -d ${D}${sysconfdir}/game-engine
    install -m 0644 ${WORKDIR}/config/game_engine.json ${D}${sysconfdir}/game-engine/game_engine.json

    install -d ${D}${systemd_unitdir}/system
    install -m 0644 ${WORKDIR}/game-engine.service ${D}${systemd_unitdir}/system/game-engine.service
}

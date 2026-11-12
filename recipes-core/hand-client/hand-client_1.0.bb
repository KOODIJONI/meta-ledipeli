SUMMARY = "Python IPC client library for hand-tracker service"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://hand_client.py \
"

S = "${WORKDIR}"

# Inherit python3native so python site-package variables resolve correctly
inherit python3native

RDEPENDS:${PN} += "\
    python3-core \
    python3-threading \
    python3-json \
"

do_install() {
    # Install into the proper python3 site-packages directory
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}
    install -m 0644 ${WORKDIR}/hand_client.py ${D}${PYTHON_SITEPACKAGES_DIR}/hand_client.py
}

# Explicitly tell BitBake to ship this file in the package manifest
FILES:${PN} += " \
    ${PYTHON_SITEPACKAGES_DIR}/hand_client.py \
"

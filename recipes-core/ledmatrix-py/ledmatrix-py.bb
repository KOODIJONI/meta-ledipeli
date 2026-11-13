
SUMMARY = "Python ctypes wrapper for LED Matrix driver"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/GPL-2.0-only;md5=801f80980d171dd6425610833a22dbe6"

SRC_URI = " \
    file://ledmatrix_bindings.py \
    file://ledmatrix.py \
"

S = "${WORKDIR}"

inherit python3targetconfig

do_compile() {
    :
}

do_install() {
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}

    install -m 0644 ${S}/ledmatrix_bindings.py \
        ${D}${PYTHON_SITEPACKAGES_DIR}/

    install -m 0644 ${S}/ledmatrix.py \
        ${D}${PYTHON_SITEPACKAGES_DIR}/
}

FILES:${PN} += " \
    ${PYTHON_SITEPACKAGES_DIR}/ledmatrix.py \
    ${PYTHON_SITEPACKAGES_DIR}/ledmatrix_bindings.py \
"

RDEPENDS:${PN} += " \
    python3-core \
    python3-ctypes \
"


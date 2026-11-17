SUMMARY = "Interrupt-driven GPIO button library with callbacks (libgpiod v2)"
DESCRIPTION = "Python module that listens for button presses/releases on GPIO lines \
using kernel edge events and calls user-supplied callbacks."
SECTION = "devel/python"

LICENSE = "CLOSED"

SRC_URI = " \
    file://gpio_buttons.py \
"

S = "${WORKDIR}"

inherit python3-dir

do_install() {
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}
    install -m 0644 ${S}/gpio_buttons.py ${D}${PYTHON_SITEPACKAGES_DIR}/gpio_buttons.py
}

PACKAGES = "${PN} ${PN}-example"

FILES:${PN} = "${PYTHON_SITEPACKAGES_DIR}/gpio_buttons.py"

RDEPENDS:${PN} = "python3-core python3-threading python3-gpiod"
RDEPENDS:${PN}-example = "${PN}"

BBCLASSEXTEND = "native nativesdk"
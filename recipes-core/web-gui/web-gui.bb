SUMMARY = "Pre-built Web GUI"
LICENSE = "CLOSED"

SRC_URI = "file://dist"

S = "${WORKDIR}"

# Skip unnecessary compile/configure tasks
do_configure[noexec] = "1"
do_compile[noexec] = "1"

FILES:${PN} += "${datadir}/nginx/html/*"

do_install() {
    install -d ${D}${datadir}/nginx/html
    cp -r ${WORKDIR}/dist/* ${D}${datadir}/nginx/html/
}

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://nginx.conf"

do_install:append() {
    install -m 0644 ${WORKDIR}/nginx.conf ${D}${sysconfdir}/nginx/nginx.conf
}


SUMMARY = "LED Matrix driver library"
DESCRIPTION = "C library for controlling an LED matrix"
LICENSE = "CLOSED"

SRC_URI = " \
    file://args.c \
    file://args.h \
    file://color.c \
    file://color.h \
    file://config.c \
    file://config.h \
    file://matrix.c \
    file://matrix.h \
    file://matrix_config.json \
    file://lib/cJSON/cJSON.c \
    file://lib/cJSON/cJSON.h \
"

S = "${WORKDIR}"

do_compile() {
    ${CC} ${CPPFLAGS} ${CFLAGS} -std=c99 -fPIC \
        -I${S}/lib/cJSON \
        -shared \
        -Wl,-soname,libledmatrix.so.1 \
        -o libledmatrix.so.1 \
        ${S}/args.c \
        ${S}/color.c \
        ${S}/config.c \
        ${S}/matrix.c \
        ${S}/lib/cJSON/cJSON.c \
        ${LDFLAGS}
}

do_install() {
    install -d ${D}${libdir}
    install -d ${D}${includedir}/ledmatrix-driver
    install -d ${D}${sysconfdir}/ledmatrix-driver

    install -m 0755 ${S}/libledmatrix.so.1 \
        ${D}${libdir}/libledmatrix.so.1

    ln -s libledmatrix.so.1 \
        ${D}${libdir}/libledmatrix.so

    install -m 0644 ${S}/args.h \
        ${D}${includedir}/ledmatrix-driver/
    install -m 0644 ${S}/color.h \
        ${D}${includedir}/ledmatrix-driver/
    install -m 0644 ${S}/config.h \
        ${D}${includedir}/ledmatrix-driver/
    install -m 0644 ${S}/matrix.h \
        ${D}${includedir}/ledmatrix-driver/

    install -m 0644 ${S}/matrix_config.json \
        ${D}${sysconfdir}/ledmatrix-driver/
}

FILES:${PN} += " \
    ${libdir}/libledmatrix.so.* \
    ${sysconfdir}/ledmatrix-driver/matrix_config.json \
"

FILES:${PN}-dev += " \
    ${includedir}/ledmatrix-driver \
    ${libdir}/libledmatrix.so \
"


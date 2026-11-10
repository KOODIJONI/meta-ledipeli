SUMMARY = "LED Matrix driver library and test utility"
DESCRIPTION = "C library for controlling an LED matrix and accompanying executable."
LICENSE = "CLOSED"

# Avoid Pseudo path-mismatch when S = WORKDIR
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"

SRC_URI = " \
    file://src \
    file://include \
    file://internal \
    file://lib \
    file://config \
    file://tests \
"

S = "${WORKDIR}"

do_compile() {
    # 1. Compile all library sources into the shared library
    LIB_SRCS=$(ls ${S}/src/*.c)
    ${CC} ${CPPFLAGS} ${CFLAGS} -std=c99 -D_POSIX_C_SOURCE=200809L -fPIC \
        -I${S}/include \
        -I${S}/internal \
        -I${S}/lib/cJSON \
        -shared \
        -Wl,-soname,libledmatrix.so.1 \
        ${LDFLAGS} \
        -o ${WORKDIR}/libledmatrix.so.1 \
        ${LIB_SRCS} \
        ${S}/lib/cJSON/cJSON.c

    # 2. Compile the standalone test executable
    ${CC} ${CPPFLAGS} ${CFLAGS} -std=c99 -D_POSIX_C_SOURCE=200809L \
        -I${S}/include \
        -I${S}/internal \
        -I${S}/lib/cJSON \
        ${S}/tests/main.c \
        ${WORKDIR}/libledmatrix.so.1 \
        ${LDFLAGS} \
        -Wl,-rpath,/usr/lib \
        -o ${WORKDIR}/matrix_test
}

do_install() {
    install -d ${D}${libdir}
    install -d ${D}${bindir}
    install -d ${D}${includedir}/ledmatrix-driver
    install -d ${D}${sysconfdir}/ledmatrix-driver

    install -m 0755 ${WORKDIR}/libledmatrix.so.1 ${D}${libdir}/libledmatrix.so.1
    ln -sf libledmatrix.so.1 ${D}${libdir}/libledmatrix.so

    install -m 0755 ${WORKDIR}/matrix_test ${D}${bindir}/matrix_test

    install -m 0644 ${S}/include/*.h ${D}${includedir}/ledmatrix-driver/

    install -m 0644 ${S}/config/matrix_config.json \
        ${D}${sysconfdir}/ledmatrix-driver/
}

FILES:${PN} += " \
    ${libdir}/libledmatrix.so.* \
    ${bindir}/matrix_test \
    ${sysconfdir}/ledmatrix-driver/matrix_config.json \
"

FILES:${PN}-dev += " \
    ${includedir}/ledmatrix-driver \
    ${libdir}/libledmatrix.so \
"

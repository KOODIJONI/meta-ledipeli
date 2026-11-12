SUMMARY = "Google MediaPipe esikäännetty Python-paketti"
HOMEPAGE = "https://google.com"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/Apache-2.0;md5=89aea4e17d99a7cacdbeed46a0096b10"

# Haetaan valmis wheel PyPI-palvelimelta
SRC_URI = "https://files.pythonhosted.org/packages/50/0d/02afdfe0e2c4c1d9a80b7a2d65951cdb82438a22ea76bb0a65e0c3d8a36f/mediapipe-1.2.2-py3-none-manylinux_2_28_aarch64.whl"
SRC_URI[sha256sum] = "9837dc18ac903a34b4e46aa56eadbdb2648a8b66ab9d73202118e77e893edcb8"

inherit python3native python3-dir

S = "${WORKDIR}"

do_install() {
    # Luodaan kohdehakemisto Pythonin site-packages -kansiolle imagessa
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}
    
    # Puretaan wheel-paketti (joka on zip-arkisto) suoraan WORKDIR-hakemistosta
    # Tämä käyttää puhdasta Pythonia ilman epävarmaa pip-työkalua ja ohittaa glibc-ongelmat
    nativepython3 -c "import zipfile; zipfile.ZipFile('${WORKDIR}/mediapipe-1.2.2-py3-none-manylinux_2_28_aarch64.whl').extractall('${D}${PYTHON_SITEPACKAGES_DIR}')"
}

RDEPENDS:${PN} += " \
    python3-core \
    python3-numpy \
    python3-protobuf \
    python3-opencv \
    python3-modules \
	python3-certifi \
	python3-matplotlib \
"

# Ohitetaan QA-tarkistukset valmiiksi käännetyille ARM64-binääreille (.so tiedostot)
INSANE_SKIP:${PN} = "already-stripped dev-so ldflags arch file-rdeps"

# Kertoo Yoctolle, että kaikki site-packages -hakemiston tiedostot kuuluvat tähän pakettiin
FILES:${PN} += "${PYTHON_SITEPACKAGES_DIR}/*"


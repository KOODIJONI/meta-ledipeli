SRCREV = "4.9.0"
SRCREV_contrib = "4.9.0"
SRC_URI = "git://github.com/opencv/opencv.git;protocol=https;branch=4.x \
           git://github.com/opencv/opencv_contrib.git;destsuffix=git/contrib;name=contrib;protocol=https;branch=4.x"

EXTRA_OECMAKE += " \
    -DBUILD_opencv_xfeatures2d=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DBUILD_EXAMPLES=OFF \
"

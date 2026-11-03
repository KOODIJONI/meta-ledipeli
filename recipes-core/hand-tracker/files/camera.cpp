#include "camera.hpp"
#include <opencv2/core.hpp>
#include <opencv2/videoio.hpp>

Camera::Camera(int device_id, bool simulate) : simulate_(simulate) {
    if (!simulate_) {
        cap_.open(device_id);
        if (cap_.isOpened()) {
            cap_.set(cv::CAP_PROP_FRAME_WIDTH, 640);
            cap_.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
        }
    }
}

bool Camera::isOpened() const {
    return simulate_ || cap_.isOpened();
}

bool Camera::readFrame(cv::Mat& frame) {
    if (simulate_) {
        frame.create(480, 640, CV_8UC3);
        cv::randu(frame, cv::Scalar::all(0), cv::Scalar::all(255));
        return true;
    }
    if (!cap_.isOpened()) return false;
    cap_ >> frame;
    return !frame.empty();
}
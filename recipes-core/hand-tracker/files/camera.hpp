#pragma once
#include <opencv2/opencv.hpp>

class Camera {
public:
    Camera(int device_id, bool simulate = false);
    bool isOpened() const;
    bool readFrame(cv::Mat& frame);
private:
    cv::VideoCapture cap_;
    bool simulate_;
};

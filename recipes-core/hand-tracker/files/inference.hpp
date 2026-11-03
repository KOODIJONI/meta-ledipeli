#pragma once
#include <memory>
#include <vector>
#include <string>
#include <opencv2/opencv.hpp>

#if __has_include("tensorflow/lite/interpreter.h")
#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model.h"
#endif

class HandInference {
public:
    HandInference(const std::string& model_path);
    bool initialize();
    bool runInference(const cv::Mat& frame, std::vector<float>& output_landmarks);

private:
    std::string model_path_;
    std::unique_ptr<tflite::FlatBufferModel> model_;
    tflite::ops::builtin::BuiltinOpResolver resolver_;
    std::unique_ptr<tflite::Interpreter> interpreter_;
};
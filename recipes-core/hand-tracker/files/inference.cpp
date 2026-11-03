#include "inference.hpp"
#include <iostream>
#include <cstring>

HandInference::HandInference(const std::string& model_path) : model_path_(model_path) {}

bool HandInference::initialize() {
    model_ = tflite::FlatBufferModel::BuildFromFile(model_path_.c_str());
    if (!model_) {
        std::cerr << "Failed to load model from " << model_path_ << std::endl;
        return false;
    }

    tflite::InterpreterBuilder(*model_, resolver_)(&interpreter_);
    if (!interpreter_) {
        std::cerr << "Failed to construct TFLite interpreter." << std::endl;
        return false;
    }

    if (interpreter_->AllocateTensors() != kTfLiteOk) {
        std::cerr << "Failed to allocate tensors!" << std::endl;
        return false;
    }

    return true;
}

bool HandInference::runInference(const cv::Mat& frame, std::vector<float>& output_landmarks) {
    if (!interpreter_) return false;

    cv::Mat resized, rgb;
    cv::resize(frame, resized, cv::Size(256, 256));
    cv::cvtColor(resized, rgb, cv::COLOR_BGR2RGB);

    rgb.convertTo(rgb, CV_32FC3, 1.0 / 255.0);

    float* input_tensor_ptr = interpreter_->typed_input_tensor<float>(0);
    if (!input_tensor_ptr) return false;

    std::memcpy(input_tensor_ptr, rgb.data, 256 * 256 * 3 * sizeof(float));

    if (interpreter_->Invoke() != kTfLiteOk) {
        return false;
    }

    float* output = interpreter_->typed_output_tensor<float>(0);
    int output_size = interpreter_->output_tensor(0)->bytes / sizeof(float);

    output_landmarks.assign(output, output + output_size);
    return true;
}
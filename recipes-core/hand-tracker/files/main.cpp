#include "camera.hpp"
#include "inference.hpp"
#include "ipc.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <chrono>

using Clock = std::chrono::steady_clock;

int main(int argc, char* argv[]) {
    bool simulate = (argc > 1 && std::string(argv[1]) == "--simulate");
    Camera camera(0, simulate);
    if (simulate) std::cout << "Warning: simulation mode, feeding random noise." << std::endl;

    if (!camera.isOpened()) {
        std::cerr << "Error: Could not open the webcam." << std::endl;
        return -1;
    }

    std::string model_path = "/usr/share/hand-tracker/hand_landmark_lite.tflite";
    HandInference inference(model_path);
    if (!inference.initialize()) {
        std::cerr << "Error: Failed to initialize inference engine." << std::endl;
        return -1;
    }

    UnixSocketClient ipcClient("/tmp/hand_tracker.sock");
    if (!ipcClient.connectServer()) {
        std::cout << "Warning: Could not connect to Unix Socket server. Running locally only..." << std::endl;
    }

    std::cout << "Starting main processing loop." << std::endl;
    cv::Mat frame;
    std::vector<float> landmarks;

    // FPS bookkeeping
    auto window_start = Clock::now();
    std::chrono::duration<double> inference_total{0};
    int frames_in_window = 0;

    while (true) {
        if (!camera.readFrame(frame)) {
            std::cerr << "Error: Blank frame grabbed." << std::endl;
            break;
        }

        auto t0 = Clock::now();
        bool ok = inference.runInference(frame, landmarks);
        auto t1 = Clock::now();

        inference_total += (t1 - t0);
        ++frames_in_window;

        if (ok && !landmarks.empty()) {
            ipcClient.sendData(landmarks);
        } else if (!ok) {
            std::cerr << "Inference failed!" << std::endl;
        }

        // Report once per second
        std::chrono::duration<double> elapsed = Clock::now() - window_start;
        if (elapsed.count() >= 1.0) {
            double loop_fps = frames_in_window / elapsed.count();
            double avg_inf_ms = (inference_total.count() / frames_in_window) * 1000.0;
            double inf_fps = 1000.0 / avg_inf_ms;

            std::cout << "Loop FPS: " << loop_fps
                      << " | Inference: " << avg_inf_ms << " ms (" << inf_fps << " FPS)"
                      << std::endl;

            window_start = Clock::now();
            inference_total = std::chrono::duration<double>{0};
            frames_in_window = 0;
        }
    }
    return 0;
}
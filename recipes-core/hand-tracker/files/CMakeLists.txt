cmake_minimum_required(VERSION 3.16)
project(hand-tracker CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenCV (opencv.pc exists in sysroot)
find_package(OpenCV REQUIRED)

# Find TensorFlow Lite headers and library directly in the Yocto sysroot
find_path(TFLITE_INCLUDE_DIR tensorflow/lite/interpreter.h)
find_library(TFLITE_LIBRARY NAMES tensorflow-lite libtensorflow-lite)

if(NOT TFLITE_INCLUDE_DIR OR NOT TFLITE_LIBRARY)
    message(FATAL_ERROR "TensorFlow Lite headers or library not found!")
endif()

# Executable sources
add_executable(hand-tracker
    main.cpp
    camera.cpp
    inference.cpp
    ipc.cpp
)

# Include directories and libraries
target_include_directories(hand-tracker PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${TFLITE_INCLUDE_DIR}
)

target_link_libraries(hand-tracker PRIVATE
    ${OpenCV_LIBS}
    ${TFLITE_LIBRARY}
    pthread
    dl
)

# Install rule for binary
install(TARGETS hand-tracker DESTINATION bin)
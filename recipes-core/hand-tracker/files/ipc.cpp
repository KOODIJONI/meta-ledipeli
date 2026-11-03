#include "ipc.hpp"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <iostream>
#include <cstring>

UnixSocketClient::UnixSocketClient(const std::string& socket_path) 
    : socket_path_(socket_path), sock_fd_(-1) {}

UnixSocketClient::~UnixSocketClient() {
    if (sock_fd_ >= 0) {
        close(sock_fd_);
    }
}

bool UnixSocketClient::connectServer() {
    sock_fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock_fd_ < 0) {
        std::perror("socket");
        return false;
    }

    sockaddr_un addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    std::strncpy(addr.sun_path, socket_path_.c_str(), sizeof(addr.sun_path) - 1);

    if (connect(sock_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::perror("connect");
        close(sock_fd_);
        sock_fd_ = -1;
        return false;
    }

    return true;
}

bool UnixSocketClient::sendData(const std::vector<float>& data) {
    if (sock_fd_ < 0) return false;

    size_t data_size = data.size() * sizeof(float);
    if (write(sock_fd_, &data_size, sizeof(size_t)) < 0) return false;
    if (write(sock_fd_, data.data(), data_size) < 0) return false;

    return true;
}
#pragma once
#include <string>
#include <vector>

class UnixSocketClient {
public:
    UnixSocketClient(const std::string& socket_path);
    ~UnixSocketClient();

    bool connectServer();
    bool sendData(const std::vector<float>& data);

private:
    std::string socket_path_;
    int sock_fd_;
};
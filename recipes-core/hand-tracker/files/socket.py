import os
import socket

class IPCServer:
    def __init__(self, socket_path="/tmp/hand_tracker.sock"):
        self.socket_path = socket_path
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.socket_path)
        self.server.listen(1)
        self.server.setblocking(False)
        self.conn = None

    def poll_connection(self):
        try:
            if not self.conn:
                self.conn, _ = self.server.accept()
                self.conn.setblocking(False)
        except BlockingIOError:
            pass

    def send_data(self, data_str):
        self.poll_connection()
        if self.conn:
            try:
                self.conn.sendall((data_str + "\n").encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError):
                self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()
        self.server.close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
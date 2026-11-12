#!/usr/bin/env python3
import os
import socket
import json
import threading
import queue
import time

class HandTrackerClient:
    def __init__(self, socket_path="/tmp/hand_tracker.sock"):
        """
        Initializes the background Unix Domain Socket listener for the hand tracker.
        
        Args:
            socket_path (str): Path to the IPC Unix socket file.
        """
        self.socket_path = socket_path
        self.data_queue = queue.Queue()
        self.running = True
        
        # Start the background listener daemon thread
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _listen_loop(self):
        """Internal background loop that accepts connections and reads streaming JSON payloads."""
        while self.running:
            # Clean up any stale socket file before binding
            if os.path.exists(self.socket_path):
                try:
                    os.remove(self.socket_path)
                except OSError:
                    pass

            server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server_sock.bind(self.socket_path)
                # Set permissions so the systemd service user can write to the socket
                os.chmod(self.socket_path, 0o777)
                server_sock.listen(1)

                while self.running:
                    server_sock.settimeout(0.5)
                    try:
                        conn, _ = server_sock.accept()
                    except socket.timeout:
                        continue

                    with conn:
                        buffer = ""
                        while self.running:
                            data = conn.recv(4096)
                            if not data:
                                break
                            buffer += data.decode("utf-8")
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if line.strip():
                                    try:
                                        parsed = json.loads(line)
                                        self.data_queue.put(parsed)
                                    except json.JSONDecodeError:
                                        pass
            except Exception:
                # Silently catch socket setup errors and retry
                time.sleep(0.5)
            finally:
                server_sock.close()
                if os.path.exists(self.socket_path):
                    try:
                        os.remove(self.socket_path)
                    except OSError:
                        pass

    def get_latest_state(self):
        """
        Non-blocking call to fetch the absolute newest hand tracking payload.
        Empties the queue so the game loop always consumes the most recent frame state.
        
        Returns:
            dict or None: The parsed JSON payload containing hands, gestures, and coordinates.
        """
        latest = None
        while not self.data_queue.empty():
            try:
                latest = self.data_queue.get_nowait()
            except queue.Empty:
                break
        return latest

    def stop(self):
        """Safely shuts down the background listener thread and cleans up the socket file."""
        self.running = False
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass

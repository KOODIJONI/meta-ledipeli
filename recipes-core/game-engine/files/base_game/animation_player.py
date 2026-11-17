import os

class RawBinAnimationPlayer:
    def __init__(self, bin_path, cols, rows):
        self.cols = cols
        self.rows = rows
        self.frame_size = cols * rows * 3
        self.frames = []

        # Ensure absolute path resolution
        if not os.path.isabs(bin_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bin_path = os.path.abspath(os.path.join(base_dir, "..", bin_path))

        print(f"[RawBinPlayer] Loading binary animation: {bin_path}")
        
        with open(bin_path, "rb") as f:
            while chunk := f.read(self.frame_size):
                if len(chunk) == self.frame_size:
                    self.frames.append(chunk)

        self.total_frames = len(self.frames)
        self.current_idx = 0
        if self.total_frames == 0:
            raise RuntimeError(f"Animation binary file is empty or invalid: {bin_path}")

    def get_next_frame(self):
        if self.total_frames == 0:
            return None
        frame = self.frames[self.current_idx]
        self.current_idx = (self.current_idx + 1) % self.total_frames
        return frame

    def release(self):
        self.frames.clear()

    def set_animation_path(self, bin_path: str):
        self.__init__(bin_path, self.cols, self.rows)
        return True
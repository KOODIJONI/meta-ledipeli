# games/matrix_game/matrix_game.py
import os
from games.base_game import BaseGame

class MatrixGame(BaseGame):
    def __init__(self, socket_path=None, config=None):
        super().__init__(socket_path=socket_path, config=config)
        print(f"[MatrixGame] Initialized matrix grid size: {self.rows} rows x {self.cols} cols")
        print(f"[MatrixGame] Window size: {self.width}x{self.height}")

        self.cursor_x = 0
        self.cursor_y = 0
        self.last_cursor_x = 0
        self.last_cursor_y = 0
        self.has_hand = False
        self.grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]

    def handle_input(self, hand_state):
        pos = self.get_hand_position(hand_state, index=0)
        if pos is not None:
            norm_x, norm_y = pos
            self.cursor_x = int(norm_x * (self.cols - 1))
            self.cursor_y = int(norm_y * (self.rows - 1))
            self.last_cursor_x = self.cursor_x
            self.last_cursor_y = self.cursor_y
            self.has_hand = True
        else:
            self.has_hand = False

    def update(self):
        """Compute the current matrix state from tracked hand position."""
        self.grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]

        if self.has_hand:
            cx = min(max(self.cursor_x, 0), self.cols - 1)
            cy = min(max(self.cursor_y, 0), self.rows - 1)
            self.grid[cy][cx] = "#"
            self.last_cursor_x = cx
            self.last_cursor_y = cy
        elif self.last_cursor_x is not None and self.last_cursor_y is not None:
            cx = min(max(self.last_cursor_x, 0), self.cols - 1)
            cy = min(max(self.last_cursor_y, 0), self.rows - 1)
            self.grid[cy][cx] = "#"

    def render(self):
        """Render the matrix grid to the physical LED display, with console fallback."""
        if self.led_matrix is not None:
            for y, row in enumerate(self.grid):
                for x, cell in enumerate(row):
                    if cell == "#":
                        self.set_led_pixel(x, y, 255, 255, 255)
                        print(f"Set Pixel {x} {y}")
            return

        os.system('cls' if os.name == 'nt' else 'clear')

        border = "+" + "-" * self.cols + "+"
        print(border)
        for row in self.grid:
            print("|" + "".join(row) + "|")
        print(border)

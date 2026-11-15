# games/matrix_game/matrix_game.py
import os
from games.base_game import BaseGame, Gesture

class MatrixGame(BaseGame):
    def __init__(self, config=None, mqtt_client=None):
        super().__init__(config=config, mqtt_client=mqtt_client)
        print(f"[MatrixGame] Initialized matrix grid size: {self.rows} rows x {self.cols} cols")
        print(f"[MatrixGame] Window size: {self.width}x{self.height}")

        self.cursor_x = 0
        self.cursor_y = 0
        self.last_cursor_x = 0
        self.last_cursor_y = 0
        self.has_hand = False
        self.grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        self.gesture = Gesture.UNKNOWN

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

        self.gesture = self.get_hand_gesture(hand_state)

    def render(self):
        self.render_player()
    def render_player(self):
        if self.has_hand:
            cx = min(max(self.cursor_x, 0), self.cols - 1)
            cy = min(max(self.cursor_y, 0), self.rows - 1)
            if self.gesture == Gesture.OPEN:
                self.set_led_pixel(cx, cy, 0, 0, 255)
            elif self.gesture == Gesture.CLOSED:
                self.set_led_pixel(cx, cy, 0, 255, 0)
            elif self.gesture == Gesture.POINTING:
                self.set_led_pixel(cx, cy, 255, 0, 0)
            elif self.gesture == Gesture.VICTORY:
                self.set_led_pixel(cx, cy, 255, 255, 0)
            elif self.gesture == Gesture.THUMBS_UP:
                self.set_led_pixel(cx, cy, 255, 140, 0)
            elif self.gesture == Gesture.THUMBS_DOWN:
                self.set_led_pixel(cx, cy, 115, 235, 172)
            else:
                self.set_led_pixel(cx, cy, 0, 30, 30)

            self.last_cursor_x = cx
            self.last_cursor_y = cy
        elif self.last_cursor_x is not None and self.last_cursor_y is not None:
            cx = min(max(self.last_cursor_x, 0), self.cols - 1)
            cy = min(max(self.last_cursor_y, 0), self.rows - 1)
            self.set_led_pixel(cx, cy, 30, 30, 30)


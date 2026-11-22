from base_game.base_game import BaseGame, Gesture
from config import get_matrix_size
from base_game.text_renderer import draw_text_centered
import time

DRAW_ANIM_PATH = "/bin/game-engine/assets/draw.bin"

class Draw(BaseGame):
    def __init__(
        self,
        socket_path=None,
        config=None,
        mqtt_client=None,
        mqtt_broker=None,
        state_prefix: str = "game",
        tracker=None,
    ):
        super().__init__(
            socket_path=socket_path,
            config=config,
            mqtt_client=mqtt_client,
            mqtt_broker=mqtt_broker,
            state_prefix=state_prefix,
            tracker=tracker,
        )

        self.rows, self.cols = get_matrix_size(self.config)
        self.canvas_width = max(1, self.cols - 1)
        self.canvas_height = max(1, self.rows - 1)

        self.canvas = [[None for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]

        self.prev_player_x = None
        self.prev_player_y = None
        self.player_x = None
        self.player_y = None

        self.prev_gesture = Gesture.UNKNOWN
        self.player_gesture = Gesture.UNKNOWN

        self.palette = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
        ]
        self.color_index = 0
        self.color = self.palette[self.color_index]

        self._title_duration = 9.0
        self._title_start = 0.0
        self._title_anim_fps = 15.0
        self._last_title_frame_time = 0.0
        self._current_title_frame = None
        self._restored_default_anim = False

        self._show_title()

    def _show_title(self):
        self.state = "title"
        self._restored_default_anim = False
        self._title_start = time.monotonic()
        self._last_title_frame_time = self._title_start

        if getattr(self, "anim_player", None) is not None:
            self.anim_player.set_animation_path(DRAW_ANIM_PATH)
            self.anim_player.current_idx = 0
            self._current_title_frame = self.anim_player.get_next_frame()

    def _draw_bin_frame(self, frame_bytes: bytes | None):
        if not frame_bytes or len(frame_bytes) < self.cols * self.rows * 3:
            return

        idx = 0
        for y in range(self.rows):
            for x in range(self.cols):
                r = frame_bytes[idx]
                g = frame_bytes[idx + 1]
                b = frame_bytes[idx + 2]
                idx += 3
                if r or g or b:
                    self.set_led_pixel(x, y, r, g, b)
    def _clamp_coords(self, norm_x, norm_y):
        x = int(norm_x * self.canvas_width)
        y = int(norm_y * self.canvas_height)
        x = max(0, min(self.canvas_width - 1, x))
        y = max(0, min(self.canvas_height - 1, y))
        return x, y

    def handle_input(self, hand_state):
        pos = self.get_hand_position(hand_state, index=0)
        gest = self.get_hand_gesture(hand_state, index=0)

        if pos is not None:
            norm_x, norm_y = pos
            x, y = self._clamp_coords(norm_x, norm_y)

            if self.player_x is None or self.player_y is None:
                self.prev_player_x = x
                self.prev_player_y = y
            else:
                self.prev_player_x = self.player_x
                self.prev_player_y = self.player_y

            self.player_x = x
            self.player_y = y
        else:
            self.player_x = None
            self.player_y = None
            self.prev_player_x = None
            self.prev_player_y = None

        if gest == Gesture.VICTORY and self.prev_gesture != Gesture.VICTORY:
            self.color_index = (self.color_index + 1) % len(self.palette)
            self.color = self.palette[self.color_index]

        self.prev_gesture = gest
        self.player_gesture = gest

    def update(self):
        if self.state == "title":
            if time.monotonic() - self._title_start >= self._title_duration:
                self.state = "draw"
            return
        self.draw_to_canvas()

    def draw_to_canvas(self):
        if self.player_gesture != Gesture.CLOSED or self.player_x is None or self.player_y is None:
            self.prev_player_x = None
            self.prev_player_y = None
            return

        self.draw_line_to_canvas()

    def draw_line_to_canvas(self):
        x1, y1 = self.player_x, self.player_y

        if self.prev_player_x is not None and self.prev_player_y is not None:
            x0, y0 = self.prev_player_x, self.prev_player_y
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy

            while True:
                self.canvas[y0][x0] = self.color
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy
        else:
            self.canvas[y1][x1] = self.color

        self.prev_player_x = x1
        self.prev_player_y = y1


    def render_selected_color(self):
        self.fill_rect(self.canvas_width-6,0,self.canvas_width,6,self.color[0],self.color[1],self.color[2])


    def _render_game_name(self):
        draw_text_centered(self, "Canvas",20,  (160, 160, 160), scale=2)


    def _render_title_animation(self):
        if getattr(self, "anim_player", None) is None:
            return

        now = time.monotonic()
        frame_interval = 1.0 / self._title_anim_fps
        if now - self._last_title_frame_time >= frame_interval:
            self._current_title_frame = self.anim_player.get_next_frame()
            self._last_title_frame_time = now

        self._draw_bin_frame(self._current_title_frame)

    def render(self):
        if self.state == "title":
            self._render_title_animation()
            self._render_game_name()
            return
        for x in range(self.canvas_width):
            for y in range(self.canvas_height):
                pixel = self.canvas[y][x]
                if pixel is not None:
                    self.set_led_pixel(x, y, pixel[0], pixel[1], pixel[2])

        self.render_selected_color()


        if self.player_x is not None and self.player_y is not None:
            self.set_led_pixel(self.player_x, self.player_y, 255, 255, 255) 
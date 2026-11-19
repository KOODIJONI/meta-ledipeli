import os
from base_game.base_game import BaseGame

class Animations(BaseGame):
    def __init__(self, socket_path=None, config=None, mqtt_client=None, mqtt_broker=None, state_prefix: str = "game", tracker=None):
        super().__init__(
            socket_path=socket_path,
            config=config,
            mqtt_client=mqtt_client,
            mqtt_broker=mqtt_broker,
            state_prefix=state_prefix,
            tracker=tracker
        )
        print(f"[AnimationsGame] Initialized matrix grid size: {self.rows} rows x {self.cols} cols")

        engine_cfg = self.config.get("engine", {}) if isinstance(self.config, dict) else {}
        path = engine_cfg.get("animation_path", "/usr/bin/game-engine/assets/screensaver_1.bin")
        print(f"[AnimationsGame] Loading background animation: {path}")
        self.anim_player.set_animation_path(path)

    def handle_input(self, hand_state):
        """No hand tracking needed for a pure animation player."""
        pass

    def update(self):
        """No per-tick game logic needed."""
        pass

    def render(self):
        """Fetch the next video frame and stream it directly to the matrix."""
        frame_bytes = self.anim_player.get_next_frame()
        if frame_bytes and self.led_matrix is not None:
            idx = 0
            for y in range(self.rows):
                for x in range(self.cols):
                    g_val = frame_bytes[idx]
                    r_val = frame_bytes[idx + 1]
                    b_val = frame_bytes[idx + 2]
                    self.set_led_pixel(x,y,g_val,r_val,b_val)
                    idx += 3

    def _cleanup(self):
        if getattr(self, "anim_player", None) is not None:
            self.anim_player.release()
        super()._cleanup()
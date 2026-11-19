from base_game.base_game import BaseGame, Gesture
from config import get_matrix_size

class BreakoutGame(BaseGame):
    def __init__(self, socket_path=None, config=None, mqtt_client=None, mqtt_broker=None, state_prefix: str = "game", tracker=None):
        super().__init__(
            socket_path=socket_path,
            config=config,
            mqtt_client=mqtt_client,
            mqtt_broker=mqtt_broker,
            state_prefix=state_prefix,
            tracker=tracker
        )
        self.rows, self.cols = get_matrix_size(self.config)
        self.player_x = None
        self.player_y = None
        self.player_gesture = Gesture.UNKNOWN

    def handle_input(self, hand_state):
        pos = self.get_hand_position(hand_state, index=0) #pos = 0-1
        gest = self.get_hand_gesture(hand_state, index=0)

        if pos is not None:
            norm_x, norm_y = pos
            self.player_x = int(norm_x * (self.cols - 1))
            self.player_y = int(norm_y * (self.rows - 1))

        self.gesture = gest
    
    def update(self):
        pass
    
    def render(self):
        if self.player_x is not None and self.player_y is not None:
            self.draw_line(0,0, self.cols-1, self.rows-1, 0, 255, 0)
            self.draw_line(self.player_x-5, self.player_y, self.player_x+5, self.player_y, 155, 255, 0)

class Player():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.length = 6

# games/tetris/tetris.py
from games.base_game import BaseGame


class Tetris(BaseGame):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.score = 0

        config = config or {}
        engine_config = config.get("engine", {})
        tetris_config = config.get("tetris", {})

        self.rows = int(engine_config.get("matrix_rows", self.rows))
        self.cols = int(engine_config.get("matrix_cols", self.cols))
        self.drop_interval_ms = int(tetris_config.get("drop_interval_ms", 700))

        pass
    def handle_input(self, hand_state):
        pass
    def update(self):
        """Tetris-specific physics/drop logic per frame."""
        pass

    def render(self):
        """Draw Tetris grid (terminal or GUI framework)."""
        pass

class Board():
    def __init__(self,cols,rows):
        pass

class Shape():
    def __init__(self):
        pass
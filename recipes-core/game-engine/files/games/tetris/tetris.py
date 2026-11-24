# games/tetris/tetris.py
from base_game.base_game import BaseGame, Gesture
from config import get_matrix_size

class Tetris(BaseGame):
    def __init__(self, socket_path=None, config=None, mqtt_client=None, mqtt_broker=None, state_prefix: str = "game", tracker=None):
        super().__init__(
            socket_path=socket_path,
            config=config,
            mqtt_client=mqtt_client,
            mqtt_broker=mqtt_broker,
            state_prefix=state_prefix,
            tracker=tracker
        )
        super().__init__(config=config, mqtt_client=mqtt_client)
        self.score = 0

        config = config or {}
        engine_config = config.get("engine", {})
        tetris_config = config.get("tetris", {})

        self.board = Board(10,20,2)
        self.tetromino = Tetromino()

        self.cursorX = 0
        self.cursorY = 0
        self.player_gesture = Gesture.UNKNOWN

        self.rows, self.cols = get_matrix_size(self.config)
        self.drop_interval_ms = int(tetris_config.get("drop_interval_ms", 700))

    def handle_input(self, hand_state):
        pos = self.get_hand_position(hand_state,index=0)
        gest = self.get_hand_gesture(hand_state,index=0)

        if pos is not None:
            normX, normY = pos
            self.cursorX = int(normX * (self.cols - 1))
            self.cursorY = int(normY * (self.rows - 1))

        self.player_gesture = gest
        
    
    def update(self):
        """Tetris-specific physics/drop logic per frame."""

        pass

    def render(self):
        """Draw Tetris grid (terminal or GUI framework)."""

        self.renderBoard(self.board)
        self.renderTetromino(self.cursorX, self.cursorY)
        self.set_led_pixel(self.cursorX,self.cursorY,g=0,b=0)

    def renderBoard(self, board, mult = 1):

        if mult != 1:
            grid = [[val for val in row for _ in range(mult)] for row in board.grid for _ in range(mult)]
        else:
            grid = board.grid
        grid = grid[:][board.bufferRows-1:]
        self.fill_rect(0,0,len(grid[0])+1,len(grid))
        self.fill_rect(1,1,len(grid[0]),len(grid)-1,0,0,0)
        for x in range(board.cols*mult):
            for y in range(board.rows*mult):
                if grid[y][x] != 0:
                    self.set_led_pixel(x+1,y+1,g=0,b=0)

    def renderTetromino(self,cx,cy):
        for px in range(4):
            for py in range(4):
                if self.tetromino.currentPiece[py][px] == 1:
                    self.set_led_pixel(cx+px-1,cy+py-1)
            
    

class Board():
    def __init__(self,cols,rows,bufferRows):
        self.cols = cols
        self.rows = rows
        self.bufferRows = bufferRows
        self.grid = [[0 for x in range(cols)] for y in range(rows+bufferRows)]

        

class Tetromino():
    def __init__(self):
        self.index = 1
        self.positionX = 0
        self.positionY = 0
        self.list = self.initList()
        self.currentPiece = self.list[self.index]

    def initList(self):
        return [
               [[0,0,0,0],
                [1,1,1,1],
                [0,0,0,0],
                [0,0,0,0]],
               [[0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]],
               [[0,1,0],
                [1,1,1],
                [0,0,0]],
               [[1,0,0],
                [1,1,1],
                [0,0,0]],
               [[0,0,1],
                [1,1,1],
                [0,0,0]],
               [[0,1,1],
                [1,1,0],
                [0,0,0]],
               [[1,1,0],
                [0,1,1],
                [0,0,0]]]

    def canFit(self, board):
        
        return True

    def move(self):
        
        pass

    def rotate(self):
        if self.index == 1:
            return self.currentPiece
        rotated = list(zip(*self.currentPiece[::-1]))
        if self.canFit() == False:
           return self.currentPiece
        return rotated


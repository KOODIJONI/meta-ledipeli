import time, fcntl, struct, sys, tty, termios, select, os, random

SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
W = H = 8
NUM_LEDS = W * H
SPEED = 6400000
MINES = 10

# 8 SPI bits per WS bit (800 kHz data rate)
ZERO = 0b11000000
ONE  = 0b11111000

FLIP_X = False
FLIP_Y = False
TICK = 0.15           # frame refresh / blink timing (seconds)

# colors are (R, G, B), already kept dim
HIDDEN = (0, 0, 10)
FLAG   = (60, 0, 40)
MINE   = (80, 0, 0)
CURSOR = (45, 45, 45)
BLANK  = (2, 2, 2)    # revealed, 0 neighbouring mines
NUMBERS = {
    1: (0, 60, 0),      # green
    2: (50, 50, 0),     # yellow
    3: (60, 25, 0),     # orange
    4: (70, 0, 0),      # red
    5: (60, 0, 30),     # pink
    6: (0, 60, 60),     # cyan
    7: (40, 0, 70),     # purple
    8: (60, 60, 60),    # white
}

LUT = [bytes(ONE if (v >> (7 - i)) & 1 else ZERO for i in range(8)) for v in range(256)]

def neighbours(x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if (dx or dy) and 0 <= x + dx < W and 0 <= y + dy < H:
                yield x + dx, y + dy

class Game:
    def __init__(self):
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.state = 'play'          # play / won / lost
        self.placed = False
        self.cx, self.cy = W // 2, H // 2

    def count(self, x, y):
        return sum((nx, ny) in self.mines for nx, ny in neighbours(x, y))

    def place_mines(self, sx, sy):
        safe = {(sx, sy)} | set(neighbours(sx, sy))
        cells = [(x, y) for x in range(W) for y in range(H) if (x, y) not in safe]
        self.mines = set(random.sample(cells, MINES))
        self.placed = True

    def reveal(self, x, y):
        if self.state != 'play' or (x, y) in self.flags or (x, y) in self.revealed:
            return
        if not self.placed:
            self.place_mines(x, y)
        if (x, y) in self.mines:
            self.state = 'lost'
            return
        stack = [(x, y)]
        while stack:                              # flood fill through empty cells
            cx, cy = stack.pop()
            if (cx, cy) in self.revealed or (cx, cy) in self.flags:
                continue
            self.revealed.add((cx, cy))
            if self.count(cx, cy) == 0:
                stack.extend(neighbours(cx, cy))
        if len(self.revealed) == NUM_LEDS - MINES:
            self.state = 'won'

    def toggle_flag(self, x, y):
        if self.state != 'play' or (x, y) in self.revealed:
            return
        self.flags ^= {(x, y)}

    def move(self, dx, dy):
        self.cx = max(0, min(W - 1, self.cx + dx))
        self.cy = max(0, min(H - 1, self.cy + dy))

    def cell_color(self, x, y, blink):
        pos = (x, y)
        if self.state == 'lost':
            if pos in self.mines:
                return MINE if blink else (20, 0, 0)
        if self.state == 'won':
            return (0, 70, 0) if blink else (0, 15, 0)
        if pos in self.revealed:
            n = self.count(x, y)
            return NUMBERS[n] if n else BLANK
        if pos in self.flags:
            return FLAG
        return HIDDEN

    def frame(self, blink):
        out = bytearray(8)
        pixels = [None] * NUM_LEDS
        for y in range(H):
            for x in range(W):
                c = self.cell_color(x, y, blink)
                if self.state == 'play' and (x, y) == (self.cx, self.cy) and blink:
                    c = CURSOR
                dx = W - 1 - x if FLIP_X else x
                dy = H - 1 - y if FLIP_Y else y
                pixels[dy * W + dx] = c
        for r, g, b in pixels:                    # GRB order
            out += LUT[g] + LUT[r] + LUT[b]
        out += bytes(500)
        return out

def parse_keys(data):
    keys = []
    i = 0
    while i < len(data):
        if data[i:i+2] == b'\x1b[' and i + 2 < len(data):
            keys.append({ord('A'): 'up', ord('B'): 'down',
                         ord('C'): 'right', ord('D'): 'left'}.get(data[i+2]))
            i += 3
        else:
            keys.append(chr(data[i]).lower())
            i += 1
    return keys

fd = sys.stdin.fileno()
old_term = termios.tcgetattr(fd)
game = Game()

with open('/dev/spidev0.0', 'wb', buffering=0) as spi:
    fcntl.ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack('I', SPEED))
    try:
        tty.setcbreak(fd)
        print("Arrows/WASD move | space or enter = reveal | f = flag | r = restart | q = quit")
        while True:
            blink = int(time.time() / 0.3) % 2 == 0
            spi.write(game.frame(blink))
            ready, _, _ = select.select([fd], [], [], TICK)
            if not ready:
                continue
            for key in parse_keys(os.read(fd, 32)):
                if key == 'q':
                    raise KeyboardInterrupt
                elif key == 'r':
                    game = Game()
                elif key in ('up', 'w'):      game.move(0, -1)
                elif key in ('down', 's'):    game.move(0, 1)
                elif key in ('left', 'a'):    game.move(-1, 0)
                elif key in ('right', 'd'):   game.move(1, 0)
                elif key in (' ', '\n', '\r'): game.reveal(game.cx, game.cy)
                elif key == 'f':              game.toggle_flag(game.cx, game.cy)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
        spi.write(bytearray(8) + (LUT[0] * 3) * NUM_LEDS + bytes(500))   # all LEDs off
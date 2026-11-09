import time, fcntl, struct, colorsys

SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
W = H = 8
NUM_LEDS = W * H
SPEED = 6400000

# 8 SPI bits per WS bit (800 kHz data rate)
ZERO = 0b11000000
ONE  = 0b11111000

MAX_BRIGHT = 60
SERPENTINE = False    # your matrix: every row runs left to right
FLIP_X = False        # True if the dot starts at the right side of a row
FLIP_Y = False        # True if the first row is at the bottom
CYCLE_SPEED = 0.25    # color cycles per second
SPREAD = 1.0          # 0.5 = softer gradient, 2.0 = more bands
FRAME_DELAY = 0.01

LUT = [bytes(ONE if (v >> (7 - i)) & 1 else ZERO for i in range(8)) for v in range(256)]

def led_index(x, y):
    if SERPENTINE and y % 2 == 1:
        x = W - 1 - x
    return y * W + x

def build_frame(phase):
    pixels = [(0, 0, 0)] * NUM_LEDS
    for y in range(H):
        for x in range(W):
            dx = W - 1 - x if FLIP_X else x
            dy = H - 1 - y if FLIP_Y else y
            pos = (dx + dy) / (W + H - 2)           # 0.0 at the start corner, 1.0 at the opposite one
            hue = (phase - pos * SPREAD) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            pixels[led_index(x, y)] = (int(r * MAX_BRIGHT), int(g * MAX_BRIGHT), int(b * MAX_BRIGHT))
    out = bytearray(8)
    for r, g, b in pixels:                          # GRB order
        out += LUT[g] + LUT[r] + LUT[b]
    out += bytes(500)
    return out

def clear(spi):
    out = bytearray(8)
    out += (LUT[0] * 3) * NUM_LEDS
    out += bytes(500)
    spi.write(out)

with open('/dev/spidev0.0', 'wb', buffering=0) as spi:
    fcntl.ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack('I', SPEED))
    try:
        t0 = time.time()
        while True:
            phase = ((time.time() - t0) * CYCLE_SPEED) % 1.0
            spi.write(build_frame(phase))
            time.sleep(FRAME_DELAY)
    except KeyboardInterrupt:
        clear(spi)
import time, fcntl, struct, random

SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
NUM_LEDS = 64
SPEED = 6400000

# 8 SPI bits per WS bit (800 kHz data rate)
NBITS = 8
ZERO = 0b11000000
ONE  = 0b11111000

MAX_BRIGHT = 60      # per channel, keeps current draw low (64 LEDs at full white is ~3.8 A)
ON_TIME = 0.3        # seconds lit
OFF_TIME = 0.15      # seconds dark

def encode(data):
    out = bytearray()
    bits = 0
    n = 0
    for byte in data:
        for i in range(7, -1, -1):
            bits = (bits << NBITS) | (ONE if (byte >> i) & 1 else ZERO)
            n += NBITS
            while n >= 8:
                out.append((bits >> (n - 8)) & 0xFF)
                n -= 8
                bits &= (1 << n) - 1
    return out

def show_all(spi, r, g, b):
    data = bytes((g, r, b)) * NUM_LEDS          # GRB order, same color on every LED
    spi.write(encode(data) + bytes(250))        # 250 zero bytes = ~320 us reset
    spi.flush()

def random_color():
    return tuple(random.randint(0, MAX_BRIGHT) for _ in range(3))

with open('/dev/spidev0.0', 'wb', buffering=0) as spi:
    fcntl.ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack('I', SPEED))
    try:
        while True:
            r, g, b = random_color()
            show_all(spi, r, g, b)
            time.sleep(ON_TIME)
            show_all(spi, 0, 0, 0)
            time.sleep(OFF_TIME)
    except KeyboardInterrupt:
        show_all(spi, 0, 0, 0)
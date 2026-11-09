import time, fcntl, struct

SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
NUM_LEDS = 64
SPEED = 6400000

# 5 SPI bits per WS bit (800 kHz data rate)
NBITS = 8
ZERO = 0b1100000
ONE  = 0b1111000

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

def show(spi, target, r, g, b):
    data = bytearray()
    for i in range(NUM_LEDS):
        data += bytes((g, r, b)) if i == target else bytes((0, 0, 0))
    spi.write(encode(data) + bytes(150))   # 150 zero bytes = ~300 us reset
    spi.flush()

with open('/dev/spidev0.0', 'wb', buffering=0) as spi:
    fcntl.ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack('I', SPEED))
    try:
        while True:
            for led in range(NUM_LEDS):
                show(spi, led, 20, 0, 0)
                time.sleep(0.04)
    except KeyboardInterrupt:
        show(spi, -1, 0, 0, 0)
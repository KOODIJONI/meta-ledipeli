#ifndef COLOR_H
#define COLOR_H

#include <stdint.h>

typedef struct __attribute__((packed)) {
    uint8_t r, g, b;
} RgbColor;

void color_set(RgbColor *self, uint8_t r, uint8_t g, uint8_t b);

#endif
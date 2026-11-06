
#include "color.h"

void color_set(RgbColor *self, uint8_t r, uint8_t g, uint8_t b)
{
    if (self == 0)
        return;

    self->r = r;
    self->g = g;
    self->b = b;
}

#include <stdio.h>
#include <stdint.h>

#define MEMORY_SIZE 1727

typedef struct __attribute__((packed)) 
{
    uint8_t r;
    uint8_t g;
    uint8_t b;
} RgbColor; 

uint8_t output_bus[MEMORY_SIZE][2];
RgbColor matrix[23][23];

void initMatrix();
void printMatrix();
int checkBounds(uint8_t, uint8_t);
void write_color(RgbColor *self, uint8_t, uint8_t, uint8_t);
int write_rectFill(uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
int write_line(uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
void write_all(uint8_t, uint8_t, uint8_t);


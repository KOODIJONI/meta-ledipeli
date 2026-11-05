#include <stdio.h>
#include <stdint.h>
#include "matrix.h"


void initMatrix()
{
    write_all(0,0,0);
    printf("Matrix initialized\n");
}
void printMatrix()
{
    for (int y=0;y<23;y++){
        for (int x=0; x<23;x++){
            printf("[%02x,%02x,%02x]", matrix[y][x].r, matrix[y][x].g, matrix[y][x].b);
        }
        printf("\n");
    }
}

int checkBounds(uint8_t x, uint8_t y)
{
    if ((x > 0 && x < 24) || (y > 0 && y < 24)){
        return 0;
    } else {
        return -1;
    }
}

void write_color(RgbColor *self, uint8_t r,uint8_t g,uint8_t b)
{
    self->r = r;
    self->g = g;
    self->b = b;   
}
int write_rectFill(uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, uint8_t r, uint8_t g, uint8_t b)
{
    if (x1 > x2 || y1 > y2){
        printf("Start coordinates larger than end coordinates\n");
        return -1;
    }
    if (checkBounds(x1,y1) == 0 || checkBounds(x2,y2) == 0){
            for (int y=y1;y<y2;y++){
                for (int x=x1; x<x2;x++){
                    write_color(&matrix[y][x],r,g,b);
                }
            }
            return 0;
    } else {
        printf("Out of bounds\n");
        return -1;
    }
}
void write_all(uint8_t r,uint8_t g,uint8_t b)
{
    for (int y=0;y<23;y++){
        for (int x=0; x<23;x++){
            write_color(&matrix[y][x],r,g,b);
        }
    }
}
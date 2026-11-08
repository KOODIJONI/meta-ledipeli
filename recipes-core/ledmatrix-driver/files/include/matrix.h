#ifndef MATRIX_H
#define MATRIX_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h> 

#include "color.h"

#ifndef ROWS
#define ROWS 23
#endif

#ifndef COLS
#define COLS 23
#endif

#define COLOR_BITS 8
#define OUTPUT_BUFFER_SIZE (ROWS * COLS)  
#define RGB_BITS (3 * COLOR_BITS)

#define MAX_BRIGHTNESS 255

#define BRIGHTNESS MAX_BRIGHTNESS

#ifndef SERPENTINE
#define SERPENTINE true
#endif

#ifndef MATRIX_LAYOUT
#define MATRIX_LAYOUT LAYOUT_TOP_LEFT_HORIZONTAL
#endif

#ifndef MATRIX_ROTATION
#define MATRIX_ROTATION ROTATION_0
#endif


extern bool debug;


typedef enum {
    CLOCKWISE,
    COUNTERCLOCKWISE
} SerpentineDirection;

typedef enum { 
    FIRST_CORNER,
    SECOND_CORNER,
    THIRD_CORNER,
    FOURTH_CORNER
} MatrixStartCorner;

typedef enum {
    ROTATION_0, 
    ROTATION_90,
    ROTATION_180,
    ROTATION_270
} MatrixRotation;

enum ERROR_CODES {
    OK = 0,
    ERROR_NULL_POINTER = -1,
    ERROR_OUT_OF_BOUNDS = -2,
    ERROR_INVALID_COORDINATES = -3,
    ERROR_OUT_OF_MEMORY = -4
};

typedef struct 
{
    RgbColor *colors;

    uint8_t rows;
    uint8_t cols;

    uint8_t brightness;
    bool  serpentine; 

    MatrixStartCorner start_corner;
    SerpentineDirection serpentine_dir;
    MatrixRotation rotation;
    
} Matrix;

typedef struct {
    uint8_t rows;
    uint8_t cols;
    uint8_t brightness;
    bool serpentine;
    
    MatrixRotation rotation;
    SerpentineDirection serpentine_dir;
    MatrixStartCorner start_corner;
} MatrixConfig;

//init functions
int MatrixInit(Matrix *m, const MatrixConfig *config);
int MatrixInitWithJson(Matrix *m, const char *json_path);
int MatrixValidate(const Matrix *m);

//debug functions
int MatrixPrintLogical(const Matrix *m);
int MatrixPrintIndexLogical(const Matrix *m);

int MatrixPrintPhysical(const Matrix *m);
int MatrixPrintIndexPhysical(const Matrix *m);

int MatrixPrintRawBuffer(const Matrix *m);
int MatrixCheckBounds(const Matrix *m, uint8_t x, uint8_t y);

//write functions
int MatrixWriteColor(Matrix *m, uint8_t x, uint8_t y, const RgbColor *self);
int MatrixWriteRectFill(Matrix *m, uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, RgbColor color);
int MatrixWriteLine(Matrix *m, uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, RgbColor color);
int MatrixWriteAll(Matrix *m, RgbColor color);

//getters and setters
int MatrixGetPixelIndex(const Matrix *m, uint8_t x, uint8_t y);
int MatrixSetBrightness(Matrix *m, float brightness);
float MatrixGetBrightness(Matrix *m);

int MatrixSetSerpentine(Matrix *m, bool serpentine);
bool MatrixGetSerpentine(Matrix *m);

int MatrixSetSize(Matrix *m, int rows, int cols);
int MatrixGetSize(Matrix *m, int *rows, int *cols);

//render functions
int MatrixSwapBuffers(Matrix **write, Matrix **read);
void MatrixFree(Matrix *m);


#endif // MATRIX_H
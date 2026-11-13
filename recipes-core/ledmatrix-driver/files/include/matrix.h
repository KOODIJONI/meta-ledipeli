#ifndef MATRIX_H
#define MATRIX_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "color.h"

/*
 * A panel made of a grid of identical tiles.
 *
 * Wiring (fixed for this hardware):
 *   - tiles are chained row by row, left to right, starting top-left, no serpentine
 *   - pixels inside a tile run row by row, left to right, starting top-left, no serpentine
 *
 * Physical index = tile_number * (tile_rows * tile_cols) + local_y * tile_cols + local_x
 * where tile_number = tile_y * grid_cols + tile_x
 */

#define FALLBACK_TILE_ROWS 6
#define FALLBACK_TILE_COLS 6
#define FALLBACK_GRID_ROWS 9
#define FALLBACK_GRID_COLS 9
#define FALLBACK_BRIGHTNESS 255

extern bool debug;

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

    uint8_t rows;        /* total panel height = grid_rows * tile_rows (unrotated) */
    uint8_t cols;        /* total panel width  = grid_cols * tile_cols (unrotated) */

    uint8_t tile_rows;   /* pixels per tile, vertical   */
    uint8_t tile_cols;   /* pixels per tile, horizontal */
    uint8_t grid_rows;   /* number of tiles, vertical   */
    uint8_t grid_cols;   /* number of tiles, horizontal */

    uint8_t brightness;
    MatrixRotation rotation;   /* rotation of the whole panel */
} Matrix;

typedef struct {
    uint8_t tile_rows;
    uint8_t tile_cols;
    uint8_t grid_rows;
    uint8_t grid_cols;

    uint8_t brightness;
    MatrixRotation rotation;
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
int32_t MatrixGetPixelIndex(const Matrix *m, uint8_t x, uint8_t y);
int MatrixSetBrightness(Matrix *m, float brightness);
float MatrixGetBrightness(Matrix *m);

int MatrixSetGrid(Matrix *m, int grid_rows, int grid_cols);   /* clears the buffer */
int MatrixGetSize(Matrix *m, int *rows, int *cols);           /* logical size (after rotation) */

//render functions
int MatrixSwapBuffers(Matrix **write, Matrix **read);
void MatrixFree(Matrix *m);

#endif // MATRIX_H
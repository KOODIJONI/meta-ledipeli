#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "matrix.h"
#include "config.h"

bool debug = false;

/* ---------- logical size (after whole-panel rotation) ---------- */

static inline int32_t MatrixLogicalW(const Matrix *m)
{
    return (m->rotation == ROTATION_90 || m->rotation == ROTATION_270) ? m->rows : m->cols;
}

static inline int32_t MatrixLogicalH(const Matrix *m)
{
    return (m->rotation == ROTATION_90 || m->rotation == ROTATION_270) ? m->cols : m->rows;
}

/* ---------- init ---------- */

int MatrixInit(Matrix *m, const MatrixConfig *config)
{
    if (m == NULL)
        return ERROR_NULL_POINTER;

    MatrixConfig default_config = {
        .tile_rows = FALLBACK_TILE_ROWS,
        .tile_cols = FALLBACK_TILE_COLS,
        .grid_rows = FALLBACK_GRID_ROWS,
        .grid_cols = FALLBACK_GRID_COLS,
        .brightness = FALLBACK_BRIGHTNESS,
        .rotation = ROTATION_0
    };

    if (config == NULL) config = &default_config;

    if (config->tile_rows == 0 || config->tile_cols == 0 ||
        config->grid_rows == 0 || config->grid_cols == 0)
        return ERROR_INVALID_COORDINATES;

    size_t rows = (size_t)config->grid_rows * config->tile_rows;
    size_t cols = (size_t)config->grid_cols * config->tile_cols;

    /* rows and cols are stored as uint8_t */
    if (rows > 255 || cols > 255)
        return ERROR_INVALID_COORDINATES;

    size_t count = rows * cols;

    if (count > SIZE_MAX / sizeof(RgbColor))
        return ERROR_INVALID_COORDINATES;

    RgbColor *colors = calloc(count, sizeof(RgbColor));

    if (colors == NULL) return ERROR_OUT_OF_MEMORY;

    m->colors = colors;
    m->rows = (uint8_t)rows;
    m->cols = (uint8_t)cols;
    m->tile_rows = config->tile_rows;
    m->tile_cols = config->tile_cols;
    m->grid_rows = config->grid_rows;
    m->grid_cols = config->grid_cols;
    m->brightness = config->brightness;
    m->rotation = config->rotation;

    int result = MatrixValidate(m);

    if (result != OK) {
        free(m->colors);
        m->colors = NULL;
        return result;
    }

    printf("Matrix initialized\n");

    return OK;
}

int MatrixInitWithJson(Matrix *m, const char *json_path)
{
    if (m == NULL || json_path == NULL) {
        return ERROR_NULL_POINTER;
    }

    MatrixConfig config = {0};

    int result = ConfigLoad(&config, json_path);
    if (result != OK) {
        return result;
    }

    return MatrixInit(m, &config);
}

int MatrixValidate(const Matrix *m)
{
    if (m == NULL) {
        if (debug) {
            printf("Matrix pointer is NULL\n");
        }
        return ERROR_NULL_POINTER;
    }

    if (m->rows == 0 || m->cols == 0) {
        if (debug) {
            printf("Invalid matrix dimensions: rows=%d, cols=%d\n", m->rows, m->cols);
        }
        return ERROR_INVALID_COORDINATES;
    }

    if (m->tile_rows == 0 || m->tile_cols == 0 || m->grid_rows == 0 || m->grid_cols == 0 ||
        (int)m->tile_rows * m->grid_rows != m->rows ||
        (int)m->tile_cols * m->grid_cols != m->cols) {
        if (debug) {
            printf("Invalid tile layout: tile=%dx%d grid=%dx%d panel=%dx%d\n",
                   m->tile_rows, m->tile_cols, m->grid_rows, m->grid_cols, m->rows, m->cols);
        }
        return ERROR_INVALID_COORDINATES;
    }

    return OK;
}

/* ---------- debug printing ---------- */

int MatrixPrintLogical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Logical View (Colors at [y][x]) ---\n");
    for (int y = 0; y < MatrixLogicalH(m); y++) {
        for (int x = 0; x < MatrixLogicalW(m); x++) {
            int32_t index = MatrixGetPixelIndex(m, x, y);
            if (index >= 0) {
                RgbColor color = m->colors[index];
                printf("(%3d,%3d,%3d) ", color.r, color.g, color.b);
            } else {
                printf("(ERR) ");
            }
        }
        printf("\n");
    }
    return OK;
}

int MatrixPrintIndexLogical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Logical View (Physical Indices at [y][x]) ---\n");
    for (int y = 0; y < MatrixLogicalH(m); y++) {
        for (int x = 0; x < MatrixLogicalW(m); x++) {
            int32_t index = MatrixGetPixelIndex(m, x, y);
            if (index >= 0) {
                printf("%4d ", index);
            } else {
                printf("ERR  ");
            }
        }
        printf("\n");
    }
    return OK;
}

/* One line per tile row, a blank line between tiles. */
int MatrixPrintPhysical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Physical Memory Buffer (Colors from index 0 to N-1) ---\n");
    int tile_pixels = m->tile_rows * m->tile_cols;
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        RgbColor color = m->colors[i];
        printf("[%4d]:(%3d,%3d,%3d) ", i, color.r, color.g, color.b);
        if ((i + 1) % m->tile_cols == 0) {
            printf("\n");
        }
        if ((i + 1) % tile_pixels == 0) {
            printf("\n");
        }
    }
    return OK;
}

int MatrixPrintIndexPhysical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Physical Memory Buffer (Index Mapping 0 to N-1) ---\n");
    int tile_pixels = m->tile_rows * m->tile_cols;
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        printf("%4d ", i);
        if ((i + 1) % m->tile_cols == 0) {
            printf("\n");
        }
        if ((i + 1) % tile_pixels == 0) {
            printf("\n");
        }
    }
    return OK;
}

int MatrixPrintRawBuffer(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Raw Buffer Data ---\n");
    int tile_pixels = m->tile_rows * m->tile_cols;
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        RgbColor color = m->colors[i];
        printf("%02X%02X%02X ", color.r, color.g, color.b);

        if ((i + 1) % m->tile_cols == 0) {
            printf("\n");
        }
        if ((i + 1) % tile_pixels == 0) {
            printf("\n");
        }
    }
    return OK;
}

/* ---------- bounds ---------- */

/* x, y are logical coordinates (after rotation). */
int MatrixCheckBounds(const Matrix *m, uint8_t x, uint8_t y)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    if (x < MatrixLogicalW(m) && y < MatrixLogicalH(m)) {
        return OK;
    } else {
        return ERROR_OUT_OF_BOUNDS;
    }
}

/* ---------- pixel mapping ---------- */

/*
 * Logical (x, y) -> index in the physical buffer.
 *
 * 1. undo the whole-panel rotation to get unrotated panel coords (u, v)
 * 2. split (u, v) into tile coords (tx, ty) and local coords (lx, ly)
 * 3. tiles are chained row-major, pixels inside a tile are row-major
 */
int32_t MatrixGetPixelIndex(const Matrix *m, uint8_t x, uint8_t y)
{
    if (m == NULL) {
        return ERROR_NULL_POINTER;
    }

    if (m->tile_rows == 0 || m->tile_cols == 0) {
        return ERROR_INVALID_COORDINATES;
    }

    if (x >= MatrixLogicalW(m) || y >= MatrixLogicalH(m)) {
        return ERROR_OUT_OF_BOUNDS;
    }

    const int32_t W = m->cols;
    const int32_t H = m->rows;

    int32_t u, v;
    switch (m->rotation) {
    case ROTATION_0:   u = x;         v = y;         break;
    case ROTATION_90:  u = W - 1 - y; v = x;         break;
    case ROTATION_180: u = W - 1 - x; v = H - 1 - y; break;
    case ROTATION_270: u = y;         v = H - 1 - x; break;
    default:           return ERROR_OUT_OF_BOUNDS;
    }

    const int32_t tx = u / m->tile_cols, lx = u % m->tile_cols;
    const int32_t ty = v / m->tile_rows, ly = v % m->tile_rows;

    const int32_t tile = ty * m->grid_cols + tx;
    const int32_t tile_pixels = (int32_t)m->tile_rows * m->tile_cols;

    /* Inside each tile, pixels are stored row-major in x/y order:
     * index = local_y * tile_cols + local_x
     * This must be used instead of the transposed form that accidentally
     * multiplies x by tile_rows. That transposed form only looks correct
     * for square tiles like 8x8, but breaks when the panel topology is
     * arranged as multiple tiles across a row/column. */
    return tile * tile_pixels + ly * m->tile_cols + lx;
}

/* ---------- writing ---------- */

int MatrixWriteColor(Matrix *m, uint8_t x, uint8_t y, const RgbColor *self)
{
    if (m == NULL || self == NULL) {
        return ERROR_NULL_POINTER;
    }

    int32_t index = MatrixGetPixelIndex(m, x, y);
    if (index < 0) {
        return index;
    }

    if (m->brightness == 255) {
        m->colors[index] = *self;
        return OK;
    }
    if (m->brightness == 0) {
        m->colors[index] = (RgbColor){0, 0, 0};
        return OK;
    }

    /* /255 keeps full scale exact (255 * b / 255 == b) */
    m->colors[index].r = (uint8_t)(((uint16_t)self->r * m->brightness) / 255);
    m->colors[index].g = (uint8_t)(((uint16_t)self->g * m->brightness) / 255);
    m->colors[index].b = (uint8_t)(((uint16_t)self->b * m->brightness) / 255);

    return OK;
}

int MatrixWriteRectFill(Matrix *m, uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, RgbColor color)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    if (x1 > x2 || y1 > y2) {
        printf("Start coordinates larger than end coordinates\n");
        return ERROR_OUT_OF_BOUNDS;
    }

    if (MatrixCheckBounds(m, x1, y1) == OK && MatrixCheckBounds(m, x2, y2) == OK) {
        for (int y = y1; y <= y2; y++) {
            for (int x = x1; x <= x2; x++) {
                MatrixWriteColor(m, x, y, &color);
            }
        }
        return OK;
    } else {
        printf("Out of bounds\n");
        return ERROR_OUT_OF_BOUNDS;
    }
}

int MatrixWriteLine(Matrix *m, uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, RgbColor color)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    if (MatrixCheckBounds(m, x1, y1) != OK || MatrixCheckBounds(m, x2, y2) != OK) {
        return ERROR_OUT_OF_BOUNDS;
    }

    int dx =  abs((int)x2 - (int)x1);
    int dy = -abs((int)y2 - (int)y1);
    int sx = x1 < x2 ? 1 : -1;
    int sy = y1 < y2 ? 1 : -1;
    int err = dx + dy;
    int x = x1, y = y1;

    for (;;) {
        int r = MatrixWriteColor(m, x, y, &color);
        if (r != OK) return r;
        if (x == x2 && y == y2) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x += sx; }
        if (e2 <= dx) { err += dx; y += sy; }
    }
    return OK;
}

int MatrixWriteAll(Matrix *m, RgbColor color)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    for (int y = 0; y < MatrixLogicalH(m); y++) {
        for (int x = 0; x < MatrixLogicalW(m); x++) {
            MatrixWriteColor(m, x, y, &color);
        }
    }
    return OK;
}

/* ---------- getters and setters ---------- */

int MatrixSetBrightness(Matrix *m, float brightness)
{
    if (MatrixValidate(m) != OK) return ERROR_NULL_POINTER;

    if (brightness < 0.0f || brightness > 1.0f) return ERROR_INVALID_COORDINATES;

    m->brightness = (uint8_t)(brightness * 255.0f + 0.5f);

    return OK;
}

float MatrixGetBrightness(Matrix *m)
{
    if (MatrixValidate(m) != OK) return -1.0f;
    return (float)m->brightness / 255.0f;
}

/*
 * Change the number of tiles. The buffer is reallocated and cleared,
 * because old pixels would end up in the wrong places after a reshape.
 */
int MatrixSetGrid(Matrix *m, int grid_rows, int grid_cols)
{
    if (m == NULL)
        return ERROR_NULL_POINTER;

    if (m->tile_rows == 0 || m->tile_cols == 0)
        return ERROR_INVALID_COORDINATES;

    if (grid_rows <= 0 || grid_cols <= 0)
        return ERROR_INVALID_COORDINATES;

    size_t rows = (size_t)grid_rows * m->tile_rows;
    size_t cols = (size_t)grid_cols * m->tile_cols;

    if (rows > 255 || cols > 255)
        return ERROR_INVALID_COORDINATES;

    size_t count = rows * cols;

    RgbColor *new_colors = calloc(count, sizeof(RgbColor));
    if (new_colors == NULL)
        return ERROR_OUT_OF_MEMORY;

    free(m->colors);
    m->colors = new_colors;
    m->grid_rows = (uint8_t)grid_rows;
    m->grid_cols = (uint8_t)grid_cols;
    m->rows = (uint8_t)rows;
    m->cols = (uint8_t)cols;

    return OK;
}

/* Returns the logical size (what x and y range over after rotation). */
int MatrixGetSize(Matrix *m, int *rows, int *cols)
{
    if (MatrixValidate(m) != OK) return ERROR_NULL_POINTER;
    if (rows == NULL || cols == NULL) return ERROR_NULL_POINTER;

    *rows = MatrixLogicalH(m);
    *cols = MatrixLogicalW(m);

    return OK;
}

/* ---------- render ---------- */

int MatrixSwapBuffers(Matrix **write, Matrix **read)
{
    if (write == NULL || read == NULL) {
        return ERROR_NULL_POINTER;
    }

    if (MatrixValidate(*write) != OK || MatrixValidate(*read) != OK) {
        return ERROR_NULL_POINTER;
    }

    Matrix *temp = *write;
    *write = *read;
    *read = temp;

    return OK;
}

void MatrixFree(Matrix *m)
{
    if (m == NULL)
        return;

    free(m->colors);
    m->colors = NULL;
}
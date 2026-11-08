#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "matrix.h"
#include "config.h"

int MatrixInit(Matrix *m, const MatrixConfig *config)
{
    if (m == NULL)
        return ERROR_NULL_POINTER;

    MatrixConfig default_config = {
        .rows = ROWS,
        .cols = COLS,
        .brightness = 255,
        .serpentine = false,
        .rotation = ROTATION_0,
        .serpentine_dir = CLOCKWISE,
        .start_corner = FIRST_CORNER
    };

    if (config == NULL)
        config = &default_config;

    if (config->rows == 0 || config->cols == 0)
        return ERROR_INVALID_COORDINATES;

    size_t count = (size_t)config->rows * config->cols;

    if (count > SIZE_MAX / sizeof(RgbColor))
        return ERROR_INVALID_COORDINATES;

    RgbColor *colors = calloc(count, sizeof(RgbColor));

    if (colors == NULL) return ERROR_OUT_OF_MEMORY;

    m->colors = colors;
    m->rows = config->rows;
    m->cols = config->cols;
    m->brightness = config->brightness;
    m->serpentine = config->serpentine;
    m->rotation = config->rotation;
    m->serpentine_dir = config->serpentine_dir;
    m->start_corner = config->start_corner;

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

    return OK;
}


int MatrixPrintLogical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Logical View (Colors at [y][x]) ---\n");
    for (int y = 0; y < m->rows; y++) {
        for (int x = 0; x < m->cols; x++) {
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
    for (int y = 0; y < m->rows; y++) {
        for (int x = 0; x < m->cols; x++) {
            int32_t index = MatrixGetPixelIndex(m, x, y);
            if (index >= 0) {
                printf("%3d ", index);
            } else {
                printf("ERR ");
            }
        }
        printf("\n");
    }
    return OK;
}

int MatrixPrintPhysical(const Matrix *m)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Physical Memory Buffer (Colors from index 0 to N-1) ---\n");
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        RgbColor color = m->colors[i];
        printf("[%2d]:(%3d,%3d,%3d) ", i, color.r, color.g, color.b);
        if ((i + 1) % m->rows == 0) {
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
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        printf("%3d ", i);
        if ((i + 1) % m->rows == 0) {
            printf("\n");
        }
    }
    return OK;
}

int MatrixPrintRawBuffer(const Matrix *m) {
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    printf("--- Raw Buffer Data ---\n");
    int total_pixels = m->rows * m->cols;
    for (int i = 0; i < total_pixels; i++) {
        RgbColor color = m->colors[i];
        printf("%02X%02X%02X ", color.r, color.g, color.b);
        
        // FIXED: Wrap line based on columns, not rows
        if ((i + 1) % m->cols == 0) {
            printf("\n");
        }
    }
    return OK;
}

int MatrixCheckBounds(const Matrix *m, uint8_t x, uint8_t y)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    if (x < m->cols && y < m->rows) {
        return OK;
    } else {
        return ERROR_OUT_OF_BOUNDS;
    }
}


int MatrixWriteRectFill(Matrix *m, uint8_t x1, uint8_t y1, uint8_t x2, uint8_t y2, RgbColor color)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    if (x1 > x2 || y1 > y2){
        printf("Start coordinates larger than end coordinates\n");
        return ERROR_OUT_OF_BOUNDS;
    }

    if (MatrixCheckBounds(m, x1, y1) == OK && MatrixCheckBounds(m, x2, y2) == OK){
            for (int y=y1;y<=y2;y++){
                for (int x=x1; x<=x2;x++){
                    MatrixWriteColor(m, x, y, &color);
                }
            }
            return OK;
    } else {
        printf("Out of bounds\n");
        return ERROR_OUT_OF_BOUNDS;
    }
}
int MatrixWriteAll(Matrix *m, RgbColor color)
{
    if (MatrixValidate(m) != OK) {
        return ERROR_NULL_POINTER;
    }

    for (int y=0;y<m->rows;y++){
        for (int x=0; x<m->cols;x++){
            MatrixWriteColor(m, x, y, &color);
        }
    }
    return OK;
}
static inline int32_t MatrixLogicalW(const Matrix *m)
{
    return (m->rotation == ROTATION_90 || m->rotation == ROTATION_270) ? m->rows : m->cols;
}

static inline int32_t MatrixLogicalH(const Matrix *m)
{
    return (m->rotation == ROTATION_90 || m->rotation == ROTATION_270) ? m->cols : m->rows;
}

int32_t MatrixGetPixelIndex(const Matrix *m, uint8_t x, uint8_t y)
{
    if (m == NULL) {
        return ERROR_NULL_POINTER;
    }

    const int32_t rows = m->rows;  
    const int32_t cols = m->cols;

    if (x >= MatrixLogicalW(m) || y >= MatrixLogicalH(m)) {
        return ERROR_OUT_OF_BOUNDS;
    }

    int32_t u, v;
    switch (m->rotation) {
    case ROTATION_0:   u = x;             v = y;             break;
    case ROTATION_90:  u = cols - 1 - y;  v = x;             break;
    case ROTATION_180: u = cols - 1 - x;  v = rows - 1 - y;  break;
    case ROTATION_270: u = y;             v = rows - 1 - x;  break;
    default:           return ERROR_OUT_OF_BOUNDS;
    }

    switch (m->start_corner) {
    case FIRST_CORNER:  break;                                      
    case SECOND_CORNER: v = rows - 1 - v; break;                    
    case THIRD_CORNER:  u = cols - 1 - u; v = rows - 1 - v; break;  
    case FOURTH_CORNER: u = cols - 1 - u; break;                    
    default:            return ERROR_OUT_OF_BOUNDS;
    }

    const bool corner_is_odd = (m->start_corner == FIRST_CORNER ||
                                m->start_corner == THIRD_CORNER);
    const bool row_major = ((m->serpentine_dir == CLOCKWISE) == corner_is_odd);

    if (row_major) {
        const int32_t uu = (m->serpentine && (v & 1)) ? (cols - 1 - u) : u;
        return (v * cols) + uu;
    } else {
        const int32_t vv = (m->serpentine && (u & 1)) ? (rows - 1 - v) : v;
        return (u * rows) + vv;
    }
}
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

    m->colors[index].r = (uint8_t)((uint16_t)self->r * m->brightness >> 8);
    m->colors[index].g = (uint8_t)((uint16_t)self->g * m->brightness >> 8);
    m->colors[index].b = (uint8_t)((uint16_t)self->b * m->brightness >> 8);

    return OK;
}


int MatrixSwapBuffers(Matrix **write, Matrix **read){
    if (MatrixValidate(*write) != OK || MatrixValidate(*read) != OK) {
        return ERROR_NULL_POINTER;
    }

    Matrix *temp = *write;
    *write = *read;
    *read = temp;

    return OK;
}
int MatrixSetSerpentine(Matrix *m, bool serpentine) {
    if (MatrixValidate(m) != OK) return ERROR_NULL_POINTER;
    
    m->serpentine = serpentine;
    return OK;
}

bool MatrixGetSerpentine(Matrix *m) {
    if (MatrixValidate(m) != OK) return false;
    return m->serpentine;
}

int MatrixSetSize(Matrix *m, int rows, int cols)
{
    if (m == NULL)
        return ERROR_NULL_POINTER;

    if (rows <= 0 || cols <= 0 || rows > 255 || cols > 255)
        return ERROR_INVALID_COORDINATES;

    size_t new_count = (size_t)rows * (size_t)cols;

    if (new_count > SIZE_MAX / sizeof(RgbColor))
        return ERROR_INVALID_COORDINATES;

    RgbColor *new_colors = realloc(
        m->colors,
        new_count * sizeof(RgbColor)
    );

    if (new_colors == NULL)
        return ERROR_NULL_POINTER;

    size_t old_count = (size_t)m->rows * m->cols;

    if (new_count > old_count) {
        memset(
            new_colors + old_count,
            0,
            (new_count - old_count) * sizeof(RgbColor)
        );
    }

    m->colors = new_colors;
    m->rows = (uint8_t)rows;
    m->cols = (uint8_t)cols;

    return OK;
}
int MatrixGetSize(Matrix *m, int *rows, int *cols) {
    if (MatrixValidate(m) != OK) return ERROR_NULL_POINTER;
    
    *rows = m->rows;
    *cols = m->cols;

    return OK;
}
int MatrixSetBrightness(Matrix *m, float brightness) {
    if (MatrixValidate(m) != OK) return ERROR_NULL_POINTER;
    
    if (brightness < 0.0f || brightness > 1.0f) return ERROR_INVALID_COORDINATES;

    m->brightness = (uint8_t)(brightness * 255.0f);

    return OK;
}
float MatrixGetBrightness(Matrix *m) {
    if (MatrixValidate(m) != OK) return -1.0f;
    return (float)m->brightness / 255.0f;
}

void MatrixFree(Matrix *m)
{
    if (m == NULL)
        return;

    free(m->colors);
    m->colors = NULL;
}
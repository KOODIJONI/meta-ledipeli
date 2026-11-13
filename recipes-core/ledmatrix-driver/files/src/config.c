#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "matrix.h"
#include "cJSON.h"

int ConfigLoad(MatrixConfig *config, const char *path)
{
    if (!config || !path) return ERROR_NULL_POINTER;

    /* defaults: any key missing from the JSON keeps these values */
    config->tile_rows = FALLBACK_TILE_ROWS;
    config->tile_cols = FALLBACK_TILE_COLS;
    config->grid_rows = FALLBACK_GRID_ROWS;
    config->grid_cols = FALLBACK_GRID_COLS;
    config->brightness = FALLBACK_BRIGHTNESS;
    config->rotation = ROTATION_0;

    FILE *file = fopen(path, "r");
    if (!file) return ERROR_INVALID_COORDINATES;

    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return ERROR_INVALID_COORDINATES;
    }

    long size = ftell(file);
    if (size < 0 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return ERROR_INVALID_COORDINATES;
    }

    char *data = malloc((size_t)size + 1);
    if (!data) {
        fclose(file);
        return ERROR_INVALID_COORDINATES;
    }

    size_t read = fread(data, 1, (size_t)size, file);
    fclose(file);

    if (read != (size_t)size) {
        free(data);
        return ERROR_INVALID_COORDINATES;
    }

    data[read] = '\0';

    cJSON *json = cJSON_Parse(data);
    free(data);

    if (!json) return ERROR_INVALID_COORDINATES;

    cJSON *v;

#define GET_NUMBER(key, min, max, field)                    \
    v = cJSON_GetObjectItemCaseSensitive(json, key);        \
    if (v) {                                                \
        if (!cJSON_IsNumber(v) || v->valuedouble < min ||   \
            v->valuedouble > max ||                         \
            v->valuedouble != (int)v->valuedouble) {        \
            cJSON_Delete(json);                             \
            return ERROR_INVALID_COORDINATES;               \
        }                                                   \
        config->field = (uint8_t)v->valueint;               \
    }

    GET_NUMBER("tile_rows", 1, 255, tile_rows)
    GET_NUMBER("tile_cols", 1, 255, tile_cols)
    GET_NUMBER("grid_rows", 1, 255, grid_rows)
    GET_NUMBER("grid_cols", 1, 255, grid_cols)
    GET_NUMBER("brightness", 0, 255, brightness)

#undef GET_NUMBER

    v = cJSON_GetObjectItemCaseSensitive(json, "rotation");
    if (v) {
        if (!cJSON_IsNumber(v)) {
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }

        switch (v->valueint) {
        case 0:   config->rotation = ROTATION_0; break;
        case 90:  config->rotation = ROTATION_90; break;
        case 180: config->rotation = ROTATION_180; break;
        case 270: config->rotation = ROTATION_270; break;
        default:
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }
    }

    cJSON_Delete(json);
    return OK;
}
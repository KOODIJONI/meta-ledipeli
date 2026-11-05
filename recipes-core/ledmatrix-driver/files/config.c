
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "cJSON.h"

int ConfigLoad(MatrixConfig *config, const char *path)
{
    if (!config || !path) return ERROR_NULL_POINTER;

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

    #define GET_NUMBER(key, min, max, field)                 \
        v = cJSON_GetObjectItemCaseSensitive(json, key);    \
        if (v) {                                             \
            if (!cJSON_IsNumber(v) || v->valuedouble < min || \
                v->valuedouble > max ||                     \
                v->valuedouble != (int)v->valuedouble) {    \
                cJSON_Delete(json);                         \
                return ERROR_INVALID_COORDINATES;          \
            }                                               \
            config->field = (uint8_t)v->valueint;           \
        }

    GET_NUMBER("rows", 1, 255, rows)
    GET_NUMBER("cols", 1, 255, cols)
    GET_NUMBER("brightness", 0, 255, brightness)

    v = cJSON_GetObjectItemCaseSensitive(json, "serpentine");
    if (v) {
        if (!cJSON_IsBool(v)) {
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }
        config->serpentine = cJSON_IsTrue(v);
    }

    v = cJSON_GetObjectItemCaseSensitive(json, "corner");
    if (v) {
        if (!cJSON_IsNumber(v) || v->valueint < 1 ||
            v->valueint > 4 || v->valuedouble != v->valueint) {
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }
        config->start_corner = (MatrixStartCorner)(v->valueint - 1);
    }

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

    v = cJSON_GetObjectItemCaseSensitive(json, "direction");
    if (v) {
        if (!cJSON_IsString(v)) {
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }

        if (strcmp(v->valuestring, "cw") == 0)
            config->serpentine_dir = CLOCKWISE;
        else if (strcmp(v->valuestring, "ccw") == 0)
            config->serpentine_dir = COUNTERCLOCKWISE;
        else {
            cJSON_Delete(json);
            return ERROR_INVALID_COORDINATES;
        }
    }

    cJSON_Delete(json);
    return OK;
}
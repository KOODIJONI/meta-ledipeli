#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "args.h"
#include "config.h"

int parse_args(int argc, char *argv[], MatrixConfig *config)
{
    if (!config || !argv)
        return ERROR_NULL_POINTER;

    if (argc == 2 && (!strcmp(argv[1], "--help") || !strcmp(argv[1], "-h"))) {
        printf("Usage: %s <matrix_config.json>\n", argv[0]);
        return -4;
    }

    if (argc != 2) return ERROR_INVALID_COORDINATES;

    *config = (MatrixConfig) {
        .tile_rows = FALLBACK_TILE_ROWS,
        .tile_cols = FALLBACK_TILE_COLS,

        .grid_rows = FALLBACK_GRID_ROWS,
        .grid_cols = FALLBACK_GRID_COLS,
        .brightness = FALLBACK_BRIGHTNESS,
        .rotation = ROTATION_0,
    };

    return ConfigLoad(config, argv[1]);
}
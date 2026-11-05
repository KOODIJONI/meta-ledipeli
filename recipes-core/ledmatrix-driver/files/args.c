#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "matrix.h"

int parse_args(int argc, char *argv[], MatrixConfig *config) 
{
    if (config == NULL || argv == NULL) {
        return ERROR_NULL_POINTER;
    }

    // Set default configuration values
    config->rows = ROWS;
    config->cols = COLS;
    config->brightness = MAX_BRIGHTNESS;
    config->serpentine = SERPENTINE;
    config->start_corner = FIRST_CORNER;
    config->serpentine_dir = CLOCKWISE; // Default to horizontal/row-major sweep
    config->rotation = ROTATION_0;

    for (int i = 1; i < argc; i++) {
        
        if (strcmp(argv[i], "--rows") == 0 || strcmp(argv[i], "-r") == 0) {
            if (i + 1 < argc) {
                int val = atoi(argv[++i]);
                if (val > 0 && val <= 255) config->rows = (uint8_t)val;
            }
        } 
        else if (strcmp(argv[i], "--cols") == 0 || strcmp(argv[i], "-c") == 0) {
            if (i + 1 < argc) {
                int val = atoi(argv[++i]);
                if (val > 0 && val <= 255) config->cols = (uint8_t)val;
            }
        } 
        else if (strcmp(argv[i], "--brightness") == 0 || strcmp(argv[i], "-b") == 0) {
            if (i + 1 < argc) {
                int val = atoi(argv[++i]);
                if (val >= 0 && val <= 255) config->brightness = (uint8_t)val;
            }
        } 
        else if (strcmp(argv[i], "--serpentine") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "true") == 0 || strcmp(argv[i], "1") == 0) {
                    config->serpentine = true;
                } else {
                    config->serpentine = false;
                }
            }
        }
        else if (strcmp(argv[i], "--corner") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "first") == 0 || strcmp(argv[i], "1") == 0) {
                    config->start_corner = FIRST_CORNER;
                } else if (strcmp(argv[i], "second") == 0 || strcmp(argv[i], "2") == 0) {
                    config->start_corner = SECOND_CORNER;
                } else if (strcmp(argv[i], "third") == 0 || strcmp(argv[i], "3") == 0) {
                    config->start_corner = THIRD_CORNER;
                } else if (strcmp(argv[i], "fourth") == 0 || strcmp(argv[i], "4") == 0) {
                    config->start_corner = FOURTH_CORNER;
                }
            }
        }
        else if (strcmp(argv[i], "--direction") == 0 || strcmp(argv[i], "--dir") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "clockwise") == 0 || strcmp(argv[i], "cw") == 0) {
                    config->serpentine_dir = CLOCKWISE;
                } else if (strcmp(argv[i], "counterclockwise") == 0 || strcmp(argv[i], "ccw") == 0) {
                    config->serpentine_dir = COUNTERCLOCKWISE;
                }
            }
        }
        else if (strcmp(argv[i], "--rotation") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "0") == 0) {
                    config->rotation = ROTATION_0;
                } else if (strcmp(argv[i], "90") == 0) {
                    config->rotation = ROTATION_90;
                } else if (strcmp(argv[i], "180") == 0) {
                    config->rotation = ROTATION_180;
                } else if (strcmp(argv[i], "270") == 0) {
                    config->rotation = ROTATION_270;
                }
            }
        }
        else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Käyttöohje:\n");
            printf("  %s [vaihtoehdot]\n\n", argv[0]);
            printf("Vaihtoehdot:\n");
            printf("  -r, --rows <1-255>         Matriisin rivimäärä\n");
            printf("  -c, --cols <1-255>         Matriisin sarakemäärä\n");
            printf("  -b, --brightness <0-255>   Kirkkaus\n");
            printf("  --serpentine <true|false>  Käärmejohdotus käytössä\n");
            printf("  --corner <1-4|first..>     Aloituskulma (1-4)\n");
            printf("  --direction <cw|ccw>       Kiertosuunta / Pyyhkäisy\n");
            printf("  --rotation <0|90|180|270>  Logiikan rotaatio\n");
            return -4; 
        }
    }

    return OK;
}

#include <stdio.h>
#include "args.h"
#include "matrix.h"
#include "stdbool.h"

#ifdef DEBUG
bool debug = true;
#else
bool debug = false;
#endif

int main(int argc, char *argv[])
{
    MatrixConfig config = {0};

    int result = parse_args(argc, argv, &config);

    if (result != 0) {
        fprintf(stderr, "Error: invalid command-line arguments\n");
        return 1;
    }

    printf("Arguments parsed successfully.\n");

    Matrix read_matrix;
    Matrix write_matrix;

    result = MatrixInit(&read_matrix, &config);
    if (result != OK) {
        fprintf(stderr, "Error: failed to initialize read matrix\n");
        return 1;
    }

    result = MatrixInit(&write_matrix, &config);
    if (result != OK) {
        fprintf(stderr, "Error: failed to initialize write matrix\n");
        return 1;
    }
    int color_index = 0;
    for (int i = 0; i < read_matrix.rows; i++) {
        for (int j = 0; j < read_matrix.cols; j++) {
            RgbColor color = {(uint8_t)(color_index % 256), 0,0 };
            color_index++;
            MatrixWriteColor(&read_matrix, j, i, &color);
        }     
    }


    MatrixPrintLogical(&read_matrix);
    MatrixPrintPhysical(&read_matrix);
    MatrixPrintRawBuffer(&read_matrix);


    return 0;
}

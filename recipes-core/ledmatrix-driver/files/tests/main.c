#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "args.h"
#include "matrix.h"
#include "buffer.h"

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

    // Fill read matrix with test colors
    int color_index = 0;

    for (int i = 0; i < read_matrix.rows; i++) {
        for (int j = 0; j < read_matrix.cols; j++) {
            RgbColor color = {
                (uint8_t)(color_index % 256),
                0,
                0
            };

            color_index++;

            MatrixWriteColor(&read_matrix, j, i, &color);
        }
    }

    // Initialize destination buffer
    size_t required_samples = BufferRequiredSamples(&read_matrix);

    Buffer buffer = {0};

    result = BufferInit(&buffer, required_samples);
    if (result != 0) {
        fprintf(stderr, "Error: failed to initialize buffer\n");
        return 1;
    }

    // Convert matrix into PWM values
    result = MatrixToBuffer(&read_matrix, &buffer);

    if (result != 0) {
        fprintf(stderr, "Error: failed to encode matrix into buffer\n");
        BufferFree(&buffer);
        return 1;
    }

    printf("Matrix encoded successfully.\n");
    printf("Buffer samples: %zu\n", buffer.size);
    printf("Buffer capacity: %zu\n", buffer.capacity);
    printf("Buffer memory: %zu bytes\n", buffer.capacity * sizeof(uint32_t));

    // Print matrix
    MatrixPrintLogical(&read_matrix);
    MatrixPrintPhysical(&read_matrix);
    MatrixPrintRawBuffer(&read_matrix);
    
    //BufferPrintRaw(&buffer);

    //BufferPrintBin(&buffer);

    BufferFree(&buffer);

    MatrixFree(&read_matrix);
    MatrixFree(&write_matrix);
    

    return 0;
}
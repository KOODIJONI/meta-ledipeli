#ifndef BUFFER_H
#define BUFFER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#include "matrix.h"

typedef struct {
    uint32_t *data;
    size_t size;     
    size_t capacity;
} Buffer;

int BufferInit(Buffer *buffer, size_t capacity);
int MatrixToBuffer(const Matrix *m, Buffer *buffer);
void BufferClear(Buffer *buffer);
void BufferFree(Buffer *buffer);
int BufferMatrixDriverOpen(const char *interface);
int BufferSendToKernel(const Buffer *buffer);
void BufferPrintRaw(const Buffer *buffer);
void BufferPrintBin(const Buffer *buffer);
void BufferMatrixDriverClose(void);
size_t BufferRequiredSamples(const Matrix *m);
#endif // BUFFER_H
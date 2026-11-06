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

size_t BufferRequiredSamples(const Matrix *m);

int MatrixToBuffer(const Matrix *m, Buffer *buffer);

int BufferWrite(Buffer *buffer, uint32_t sample);

int BufferWriteMany(Buffer *buffer, const uint32_t *samples, size_t count);

void BufferClear(Buffer *buffer);

void BufferFree(Buffer *buffer);

void BufferPrintRaw(const Buffer *buffer);

int BufferValidate(const Buffer *buffer);

int BufferSendToKernel(const Buffer *buffer);

#endif // BUFFER_H
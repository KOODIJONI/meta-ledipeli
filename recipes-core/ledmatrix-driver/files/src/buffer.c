#include "buffer.h"
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

static int led_fd = -1;
#define RESET_WORDS 60

size_t BufferRequiredSamples(const Matrix *m) {
    if (!m) return 0;
    size_t pixel_count = (size_t)m->rows * (size_t)m->cols;
    return (pixel_count * 6) + RESET_WORDS;
}

int BufferInit(Buffer *buffer, size_t capacity) {
    if (!buffer) return ERROR_NULL_POINTER;
    
    buffer->data = (uint32_t *)malloc(capacity * sizeof(uint32_t));
    if (!buffer->data) return ERROR_OUT_OF_MEMORY;
    
    buffer->capacity = capacity;
    buffer->size = 0;
    return OK;
}
void BufferPrintRaw(const Buffer *buffer) {
    if (!buffer) return;
    
    for (size_t i = 0; i < buffer->size; i++) {
        printf("0x%08X\n", buffer->data[i]);
    }
}

void BufferPrintBin(const Buffer *buffer) {
    if (!buffer) return;
    
    for (size_t i = 0; i < buffer->size; i++) {
        uint32_t word = buffer->data[i];
        printf("[%04zu] ", i);
        
        for (int bit = 31; bit >= 0; bit--) {
            putchar((word & (1U << bit)) ? '1' : '0');
            
            if (bit % 8 == 0 && bit > 0) {
                putchar(' ');
            }
        }
        putchar('\n');
    }
}

int MatrixToBuffer(const Matrix *m, Buffer *buffer) {
    if (!m || !buffer) return ERROR_NULL_POINTER;

    size_t required = BufferRequiredSamples(m);
    if (buffer->capacity < required) {
        return ERROR_OUT_OF_MEMORY;
    }

    buffer->size = 0;
    size_t pixel_count = (size_t)m->rows * (size_t)m->cols;
    size_t out_idx = 0;

    uint32_t current_word = 0;
    int byte_shift = 24;

    for (size_t i = 0; i < pixel_count; i++) {
        int physical_idx = MatrixGetPixelIndex(m, i % m->cols, i / m->cols);
        if (physical_idx < 0) {
            return physical_idx; 
        }

        RgbColor col = m->colors[physical_idx];

        uint8_t scaled_r = (uint8_t)(((uint32_t)col.r * m->brightness) / 255);
        uint8_t scaled_g = (uint8_t)(((uint32_t)col.g * m->brightness) / 255);
        uint8_t scaled_b = (uint8_t)(((uint32_t)col.b * m->brightness) / 255);

        uint8_t channels[3] = { scaled_g, scaled_r, scaled_b };

        for (int c = 0; c < 3; c++) {
            uint8_t val = channels[c];
            for (int bit = 7; bit >= 0; bit--) {
                // 6.4 MHz mapping: Logical 1 = 0xFC (11111100), Logical 0 = 0xC0 (11000000)
                uint8_t spi_byte = (val & (1 << bit)) ? 0xFC : 0xC0;

                current_word |= ((uint32_t)spi_byte << byte_shift);
                byte_shift -= 8;

                if (byte_shift < 0) {
                    buffer->data[out_idx++] = current_word;
                    current_word = 0;
                    byte_shift = 24;
                }
            }
        }
    }

    for (int r = 0; r < RESET_WORDS; r++) {
        buffer->data[out_idx++] = 0x00000000;
    }

    buffer->size = out_idx;
    return OK;
}

void BufferClear(Buffer *buffer) {
    if (buffer) {
        buffer->size = 0;
    }
}

void BufferFree(Buffer *buffer) {
    if (buffer) {
        free(buffer->data);
        buffer->data = NULL;
        buffer->size = 0;
        buffer->capacity = 0;
    }
}

int BufferMatrixDriverOpen(const char *interface) {
    if (led_fd >= 0) return OK; 
    
    led_fd = open(interface, O_WRONLY);
    if (led_fd < 0) {
        return ERROR_NULL_POINTER; 
    }
    return OK;
}

int BufferSendToKernel(const Buffer *buffer) {
    if (!buffer || led_fd < 0) return ERROR_NULL_POINTER;

    ssize_t bytes_to_write = buffer->size * sizeof(uint32_t);
    ssize_t written = write(led_fd, buffer->data, bytes_to_write);

    if (written != bytes_to_write) {
        return ERROR_OUT_OF_BOUNDS;
    }

    return OK;
}

void BufferMatrixDriverClose(void) {
    if (led_fd >= 0) {
        close(led_fd);
        led_fd = -1;
    }
}
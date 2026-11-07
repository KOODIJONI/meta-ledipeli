
#include "buffer.h"

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>          /* printf, perror */
#include <errno.h>

#define PWM_CLK_HZ        100000000ULL
#define PWM_PERIOD_TICKS  120U        /* 1200 ns */
#define T0H_NS            300U
#define T1H_NS            800U
#define RESET_PWM_PERIODS 300U        /* 300 x 1.2 us = 360 us, must exceed 280 us */

#define NS_TO_TICKS(ns)   ((uint32_t)(((uint64_t)(ns) * PWM_CLK_HZ + 500000000ULL) / 1000000000ULL))

#define PWM_DUTY_ZERO     NS_TO_TICKS(T0H_NS)      /* 30 */
#define PWM_DUTY_ONE      NS_TO_TICKS(T1H_NS)      /* 80 */

_Static_assert(PWM_DUTY_ONE < PWM_PERIOD_TICKS, "duty must be less than period");


#define BITS_PER_COLOR      8U
#define COLORS_PER_PIXEL    3U
#define PWM_VALUES_PER_PIXEL (BITS_PER_COLOR * COLORS_PER_PIXEL)



int BufferInit(Buffer *buffer, size_t capacity)
{
    if (buffer == NULL || capacity == 0) return -1;

    if (capacity > SIZE_MAX / sizeof(uint32_t)) return -1;

    buffer->data = malloc(capacity * sizeof(uint32_t));

    if (buffer->data == NULL) {
        buffer->size = 0;
        buffer->capacity = 0;
        return -1;
    }

    buffer->size = 0;
    buffer->capacity = capacity;

    return 0;
}

int BufferValidate(const Buffer *buffer)
{
    if (buffer == NULL || buffer->data == NULL)
        return -1;

    if (buffer->size == 0) return -1;

    for (size_t i = 0; i < buffer->size; i++) {
        uint32_t value = buffer->data[i];

        if (value != PWM_DUTY_ZERO &&
            value != PWM_DUTY_ONE &&
            value != 0)
            return -1;
    }

    return 0;
}

size_t BufferRequiredSamples(const Matrix *m)
{
    if (m == NULL) return 0;

    if (MatrixValidate(m) != OK) return 0;

    size_t pixel_count = (size_t)m->rows * m->cols;

    if (pixel_count > (SIZE_MAX - RESET_PWM_PERIODS) / PWM_VALUES_PER_PIXEL) return 0;

    return (pixel_count * PWM_VALUES_PER_PIXEL) + RESET_PWM_PERIODS;
}


int BufferWrite(Buffer *buffer, uint32_t sample)
{
    if (buffer == NULL || buffer->data == NULL) return -1;

    if (buffer->size >= buffer->capacity) return -1;

    buffer->data[buffer->size++] = sample;

    return 0;
}


int BufferWriteMany(
    Buffer *buffer,
    const uint32_t *samples,
    size_t count)
{
    if (buffer == NULL || buffer->data == NULL) return -1;

    if (samples == NULL && count > 0) return -1;

    if (buffer->size > buffer->capacity) return -1;

    if (count > buffer->capacity - buffer->size) return -1;

    if (count > 0) {
        memcpy(
            &buffer->data[buffer->size],
            samples,
            count * sizeof(uint32_t)
        );
    }

    buffer->size += count;

    return 0;
}

static int BufferEncodeByte(
    Buffer *buffer,
    uint8_t value)
{
    for (int bit = 7; bit >= 0; bit--) {

        uint32_t duty =
            (value & (1U << bit))
                ? PWM_DUTY_ONE
                : PWM_DUTY_ZERO;

        if (BufferWrite(buffer, duty) != 0)
            return -1;
    }

    return 0;
}

int MatrixToBuffer(const Matrix *m, Buffer *buffer)
{
    if (m == NULL || buffer == NULL || buffer->data == NULL) return -1;

    if (MatrixValidate(m) != OK) return -1;

    size_t required = BufferRequiredSamples(m);

    if (required == 0 || buffer->capacity < required) return -1;

    BufferClear(buffer);

    size_t pixel_count = (size_t)m->rows * m->cols;

    for (size_t i = 0; i < pixel_count; i++) {

        const RgbColor *color = &m->colors[i];


        if (BufferEncodeByte(buffer, color->g) != 0) goto error;

        if (BufferEncodeByte(buffer, color->r) != 0) goto error;

        if (BufferEncodeByte(buffer, color->b) != 0) goto error;
    }

    for (size_t i = 0; i < RESET_PWM_PERIODS; i++) {

        if (BufferWrite(buffer, 0) != 0) goto error;
    }

    return 0;

error:
    BufferClear(buffer);
    return -1;
}

void BufferClear(Buffer *buffer)
{
    if (buffer == NULL) return;

    buffer->size = 0;
}

void BufferFree(Buffer *buffer)
{
    if (buffer == NULL) return;

    free(buffer->data);

    buffer->data = NULL;
    buffer->size = 0;
    buffer->capacity = 0;
}

void BufferPrintRaw(const Buffer *buffer)
{
    if (buffer == NULL || buffer->data == NULL) return;

    printf("--- Raw Buffer Data ---\n");
    for (size_t i = 0; i < buffer->size; i++) {
        printf("%02X ", buffer->data[i]);
        if ((i + 1) % 16 == 0) {
            printf("\n");
        }
    }
    if (buffer->size % 16 != 0) {
        printf("\n");
    }
}

int BufferSendToKernel(const Buffer *buffer, const char *interface)
{
    if (buffer == NULL || buffer->data == NULL || interface == NULL) return -1;

    int fd = open(interface, O_WRONLY);
    if (fd < 0) { perror("open"); return -1; }

    const uint8_t *p = (const uint8_t *)buffer->data;
    size_t left = buffer->size * sizeof(uint32_t);

    while (left > 0) {
        ssize_t n = write(fd, p, left);
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("write");
            close(fd);
            return -1;
        }
        p += n;
        left -= (size_t)n;
    }
    close(fd);
    return 0;
}

#ifndef _LEDMATRIX_KERNEL_H
#define _LEDMATRIX_KERNEL_H

#include <linux/types.h>
#include <linux/spi/spi.h>
#include <linux/cdev.h>
#include <linux/mutex.h>
#include <linux/completion.h>
#include <linux/atomic.h>

#define LED_NUM_CHANNELS 4

struct ledmatrix_dev {
    struct device *dev;
    struct cdev cdev;
    struct class *class;
    dev_t devt;
    
    struct spi_device *spi_channels[LED_NUM_CHANNELS];
    
    uint8_t *dma_tx_buf;
    size_t max_total_buf_size;
    
    struct mutex lock;
};

int ledmatrix_dispatch_channels(struct ledmatrix_dev *priv, const uint8_t __user *user_buf, size_t total_len);

#endif // _LEDMATRIX_KERNEL_H
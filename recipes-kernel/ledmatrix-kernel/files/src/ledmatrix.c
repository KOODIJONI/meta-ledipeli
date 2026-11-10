#include "ledmatrix.h"
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/delay.h>

struct ledmatrix_async_context {
    struct completion done;
    atomic_t inflight;
};

static void ledmatrix_spi_complete(void *arg)
{
    struct ledmatrix_async_context *ctx = arg;
    if (atomic_dec_and_test(&ctx->inflight)) {
        complete(&ctx->done);
    }
}

int ledmatrix_dispatch_channels(struct ledmatrix_dev *priv, const uint8_t __user *user_buf, size_t total_len)
{
    size_t channel_len;
    int i, submitted_count = 0, ret = 0;
    
    struct ledmatrix_async_context ctx;
    struct spi_message msgs[LED_NUM_CHANNELS];
    struct spi_transfer xfers[LED_NUM_CHANNELS];

    if (total_len % LED_NUM_CHANNELS != 0) {
        dev_err(priv->dev, "Buffer length not divisible by channels\n");
        return -EINVAL;
    }

    channel_len = total_len / LED_NUM_CHANNELS;

    if (total_len > priv->max_total_buf_size) {
        dev_err(priv->dev, "Buffer size exceeds maximum allowed\n");
        return -ENOMEM;
    }

    if (copy_from_user(priv->dma_tx_buf, user_buf, total_len))
        return -EFAULT;

    init_completion(&ctx.done);
    atomic_set(&ctx.inflight, 0);

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        if (!priv->spi_channels[i])
            continue;

        uint8_t *channel_ptr = priv->dma_tx_buf + (i * channel_len);

        xfers[i] = (struct spi_transfer){
            .tx_buf = channel_ptr,
            .len = channel_len,
            .speed_hz = 6400000,
            .bits_per_word = 8,
        };

        spi_message_init(&msgs[i]);
        spi_message_add_tail(&xfers[i], &msgs[i]);

        msgs[i].complete = ledmatrix_spi_complete;
        msgs[i].context = &ctx;

        atomic_inc(&ctx.inflight);
        submitted_count++;

        ret = spi_async(priv->spi_channels[i], &msgs[i]);
        if (ret < 0) {
            dev_err(priv->dev, "Async SPI submit failed on channel %d: %d\n", i, ret);
            atomic_dec(&ctx.inflight);
            break;
        }
    }

    if (submitted_count == 0) {
        return -ENODEV;
    }

    wait_for_completion(&ctx.done);

    return ret < 0 ? ret : total_len;
}

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Joni Mayra");
MODULE_DESCRIPTION("LED Matrix Kernel Buffer Receiver Driver");
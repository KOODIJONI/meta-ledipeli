
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/of.h>
#include <linux/spi/spi.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/mutex.h>
#include <linux/completion.h>
#include <linux/atomic.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/wait.h>

#include "ledmatrix.h"

static const struct file_operations ledmatrix_fops;

struct ledmatrix_async_context {
    struct completion done;
    atomic_t pending;
};

struct ledmatrix_async_slot {
    struct ledmatrix_async_context *ctx;
    struct spi_message *msg;
    int status;
};

struct ledmatrix_dev {
    struct spi_device *spi_channels[LED_NUM_CHANNELS];

    dev_t devt;
    struct cdev cdev;
    struct class *class;
    struct device *device;

    bool devt_allocated;
    bool cdev_added;

    bool ready;
    bool transmitting;
    bool removing;

    struct mutex lock;
    wait_queue_head_t idle_wait;
};

static struct ledmatrix_dev ledmatrix;

static void ledmatrix_spi_complete(void *arg)
{
    struct ledmatrix_async_slot *slot = arg;

    slot->status = slot->msg->status;

    if (atomic_dec_and_test(&slot->ctx->pending))
        complete(&slot->ctx->done);
}

static void ledmatrix_finish_transmission(void)
{
    mutex_lock(&ledmatrix.lock);

    ledmatrix.transmitting = false;

    mutex_unlock(&ledmatrix.lock);

    wake_up_all(&ledmatrix.idle_wait);
}

static void ledmatrix_unregister_chrdev_locked(void)
{
    ledmatrix.ready = false;

    if (ledmatrix.device) {
        device_destroy(ledmatrix.class, ledmatrix.devt);
        ledmatrix.device = NULL;
    }

    if (ledmatrix.class) {
        class_destroy(ledmatrix.class);
        ledmatrix.class = NULL;
    }

    if (ledmatrix.cdev_added) {
        cdev_del(&ledmatrix.cdev);
        ledmatrix.cdev_added = false;
    }

    if (ledmatrix.devt_allocated) {
        unregister_chrdev_region(ledmatrix.devt, 1);
        ledmatrix.devt_allocated = false;
    }
}

static int ledmatrix_register_chrdev_locked(void)
{
    int i;
    int ret;

    if (ledmatrix.device)
        return 0;

    if (ledmatrix.removing)
        return -EBUSY;

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        if (!ledmatrix.spi_channels[i])
            return 0;
    }

    ret = alloc_chrdev_region(
        &ledmatrix.devt, 0, 1, "ledmatrix");

    if (ret)
        return ret;

    ledmatrix.devt_allocated = true;

    cdev_init(&ledmatrix.cdev, &ledmatrix_fops);
    ledmatrix.cdev.owner = THIS_MODULE;

    ret = cdev_add(&ledmatrix.cdev, ledmatrix.devt, 1);
    if (ret)
        goto error;

    ledmatrix.cdev_added = true;

    ledmatrix.class = class_create("ledmatrix");

    if (IS_ERR(ledmatrix.class)) {
        ret = PTR_ERR(ledmatrix.class);
        ledmatrix.class = NULL;
        goto error;
    }

    ledmatrix.device = device_create(
        ledmatrix.class,
        NULL,
        ledmatrix.devt,
        NULL,
        "ledmatrix");

    if (IS_ERR(ledmatrix.device)) {
        ret = PTR_ERR(ledmatrix.device);
        ledmatrix.device = NULL;
        goto error;
    }

    ledmatrix.ready = true;

    pr_info("ledmatrix: created /dev/ledmatrix\n");

    return 0;

error:
    ledmatrix_unregister_chrdev_locked();
    return ret;
}

static ssize_t ledmatrix_write(
    struct file *file,
    const char __user *user_buf,
    size_t total_len,
    loff_t *offset)
{
    struct ledmatrix_async_context ctx;
    struct ledmatrix_async_slot slots[LED_NUM_CHANNELS];
    struct spi_message msgs[LED_NUM_CHANNELS];
    struct spi_transfer xfers[LED_NUM_CHANNELS];

    struct spi_device *spi_channels[LED_NUM_CHANNELS];

    uint8_t *tx_buf = NULL;

    size_t channel_len;
    int i;
    int ret;
    int first_error = 0;

    (void)file;
    (void)offset;

    if (!total_len)
        return 0;

    if (total_len > LEDMATRIX_MAX_TOTAL_BUF_SIZE)
        return -EMSGSIZE;

    if (total_len % LED_NUM_CHANNELS)
        return -EINVAL;

    channel_len = total_len / LED_NUM_CHANNELS;

    if (mutex_lock_interruptible(&ledmatrix.lock))
        return -ERESTARTSYS;

    if (!ledmatrix.ready || ledmatrix.removing) {
        mutex_unlock(&ledmatrix.lock);
        return -ENODEV;
    }

    if (ledmatrix.transmitting) {
        mutex_unlock(&ledmatrix.lock);
        return -EBUSY;
    }

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        if (!ledmatrix.spi_channels[i]) {
            mutex_unlock(&ledmatrix.lock);
            return -ENODEV;
        }

        spi_channels[i] = ledmatrix.spi_channels[i];
    }

    ledmatrix.transmitting = true;

    mutex_unlock(&ledmatrix.lock);

    tx_buf = kmalloc(total_len, GFP_KERNEL);

    if (!tx_buf) {
        ret = -ENOMEM;
        goto finish;
    }

    if (copy_from_user(tx_buf, user_buf, total_len)) {
        ret = -EFAULT;
        goto finish;
    }

    init_completion(&ctx.done);
    atomic_set(&ctx.pending, LED_NUM_CHANNELS);

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        struct spi_device *spi = spi_channels[i];

        slots[i].ctx = &ctx;
        slots[i].msg = &msgs[i];
        slots[i].status = -EINPROGRESS;

        xfers[i] = (struct spi_transfer) {
            .tx_buf = tx_buf + (i * channel_len),
            .len = channel_len,
            .speed_hz = spi->max_speed_hz,
            .bits_per_word = 8,
        };

        spi_message_init(&msgs[i]);
        spi_message_add_tail(&xfers[i], &msgs[i]);

        msgs[i].complete = ledmatrix_spi_complete;
        msgs[i].context = &slots[i];
    }

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        ret = spi_async(spi_channels[i], &msgs[i]);

        if (ret < 0) {
            slots[i].status = ret;

            pr_err(
                "ledmatrix: SPI channel %d submission failed: %d\n",
                i,
                ret
            );

            if (atomic_dec_and_test(&ctx.pending))
                complete(&ctx.done);
        }
    }

    wait_for_completion(&ctx.done);

    for (i = 0; i < LED_NUM_CHANNELS; i++) {
        if (slots[i].status < 0 && !first_error)
            first_error = slots[i].status;
    }

    if (first_error) {
        ret = first_error;
        goto finish;
    }

    ret = total_len;

finish:
    kfree(tx_buf);

    ledmatrix_finish_transmission();

    return ret;
}

static const struct file_operations ledmatrix_fops = {
    .owner = THIS_MODULE,
    .write = ledmatrix_write,
    .open = nonseekable_open,
    .llseek = no_llseek,
};

static int ledmatrix_probe(struct spi_device *spi)
{
    struct ledmatrix_dev *priv = &ledmatrix;
    unsigned int channel;
    int ret;

    ret = of_property_read_u32(
        spi->dev.of_node,
        "joni,channel",
        &channel);

    if (ret)
        return ret;

    if (channel >= LED_NUM_CHANNELS)
        return -EINVAL;

    spi->mode = SPI_MODE_0;
    spi->bits_per_word = 8;

    ret = spi_setup(spi);

    if (ret)
        return ret;

    mutex_lock(&priv->lock);

    if (priv->removing) {
        mutex_unlock(&priv->lock);
        return -EBUSY;
    }

    if (priv->spi_channels[channel]) {
        mutex_unlock(&priv->lock);
        return -EBUSY;
    }

    priv->spi_channels[channel] = spi;

    spi_set_drvdata(spi, priv);

    ret = ledmatrix_register_chrdev_locked();

    if (ret) {
        priv->spi_channels[channel] = NULL;
        spi_set_drvdata(spi, NULL);
    }

    mutex_unlock(&priv->lock);

    if (!ret) {
        dev_info(
            &spi->dev,
            "LED matrix channel %u registered\n",
            channel
        );
    }

    return ret;
}

static void ledmatrix_remove(struct spi_device *spi)
{
    struct ledmatrix_dev *priv = spi_get_drvdata(spi);
    unsigned int channel;

    if (!priv)
        return;

    mutex_lock(&priv->lock);

    priv->ready = false;
    priv->removing = true;

    mutex_unlock(&priv->lock);

    wait_event(
        priv->idle_wait,
        !READ_ONCE(priv->transmitting)
    );

    mutex_lock(&priv->lock);

    for (channel = 0; channel < LED_NUM_CHANNELS; channel++) {
        if (priv->spi_channels[channel] == spi) {
            priv->spi_channels[channel] = NULL;
            break;
        }
    }

    ledmatrix_unregister_chrdev_locked();

    priv->removing = false;

    mutex_unlock(&priv->lock);

    spi_set_drvdata(spi, NULL);

    dev_info(&spi->dev, "LED matrix channel removed\n");
}
static const struct of_device_id ledmatrix_of_match[] = {
    { .compatible = "joni,ledmatrix-channel" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, ledmatrix_of_match);

static const struct spi_device_id ledmatrix_id[] = {
    { "ledmatrix-channel", 0 },
    { {0} }
};
MODULE_DEVICE_TABLE(spi, ledmatrix_id);

static struct spi_driver ledmatrix_driver = {
    .driver = {
        .name = "ledmatrix",
        .of_match_table = ledmatrix_of_match,
    },
    .id_table = ledmatrix_id,   
    .probe = ledmatrix_probe,
    .remove = ledmatrix_remove,
};

static int __init ledmatrix_init(void)
{
    mutex_init(&ledmatrix.lock);
    init_waitqueue_head(&ledmatrix.idle_wait);

    return spi_register_driver(&ledmatrix_driver);
}

static void __exit ledmatrix_exit(void)
{
    spi_unregister_driver(&ledmatrix_driver);
}

module_init(ledmatrix_init);
module_exit(ledmatrix_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Joni Mayra");
MODULE_DESCRIPTION("Three-channel LED matrix SPI driver");

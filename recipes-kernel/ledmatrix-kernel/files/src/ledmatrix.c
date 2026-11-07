#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Developer");
MODULE_DESCRIPTION("Minimal PWM Buffer Kernel Receiver");

static ssize_t pwm_write(struct file *file, const char __user *buf, size_t count, loff_t *pos)
{
    uint32_t *kernel_buf;
    size_t n_samples = count / sizeof(uint32_t);
    size_t i;

    if (count % sizeof(uint32_t) != 0)
        return -EINVAL;

    kernel_buf = kmalloc(count, GFP_KERNEL);
    if (!kernel_buf)
        return -ENOMEM;

    if (copy_from_user(kernel_buf, buf, count)) {
        kfree(kernel_buf);
        return -EFAULT;
    }

    pr_info("PWM_RX: Received %zu samples\n", n_samples);
    for (i = 0; i < n_samples; i++) {
        pr_info("sample[%zu] = %u\n", i, kernel_buf[i]);
    }

    kfree(kernel_buf);
    return count;
}

static const struct file_operations pwm_fops = {
    .owner = THIS_MODULE,
    .write = pwm_write,
};

static struct miscdevice pwm_misc = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "ledmatrix", 
    .fops = &pwm_fops,
};

static int __init pwm_init(void)
{
    return misc_register(&pwm_misc);
}

static void __exit pwm_exit(void)
{
    misc_deregister(&pwm_misc);
}

module_init(pwm_init);
module_exit(pwm_exit);
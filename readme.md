# `meta-ledipeli` Yocto Setup Guide

This document provides step-by-step instructions for setting up your Yocto build environment from scratch, cloning Poky (`scarthgap`), and using the project configuration files bundled within `meta-ledipeli/projects-conf/`.

## 1. Prerequisites & Host Packages

Ensure your host system (Ubuntu/Debian recommended) has the required build packages installed:

```bash
sudo apt update
sudo apt install gawk wget git diffstat unzip texinfo gcc build-essential \
  chrpath socat cpio python3 python3-pip python3-pexpect xz-utils debianutils \
  iputils-ping python3-git python3-jinja2 libegl1-mesa libsdl1.2-dev \
  pylint xterm python3-subunit mesa-common-dev zstd liblz4-tool
```

---

## 2. Downloading Yocto (Poky) and Layers

1. **Clone the Poky repository (`scarthgap` branch):**

   ```bash
   git clone -b scarthgap git://git.yoctoproject.org/poky.git
   cd poky
   ```

2. **Clone the Raspberry Pi BSP layer (`scarthgap` branch):**

   ```bash
   git clone -b scarthgap https://github.com/agherzan/meta-raspberrypi.git
   ```

3. **Clone the OpenEmbedded  layer (`scarthgap` branch):**

   ```bash
   git clone -b scarthgap https://github.com/openembedded/meta-openembedded.git
   ```

4. **Clone or place your `meta-ledipeli` layer** into the root of the `poky` directory:

   ```bash
   git clone https://github.com/KOODIJONI/meta-ledipeli.git
   ```

---

## 3. Environment Initialization & Project Configuration

1. **Navigate to the Poky directory:**

   ```bash
   cd /path/to/poky
   ```

2. **Source the build environment:**

   ```bash
   source oe-init-build-env build
   ```

   *This creates the `build/` directory and sets environment variables.*

3. **Apply the project configuration files from `meta-ledipeli`:**

   Copy the template configuration files stored in `meta-ledipeli/projects-conf/` into your active `build/conf/` directory:

   ```bash
   cp ../meta-ledipeli/projects-conf/bblayers.conf conf/bblayers.conf
   cp ../meta-ledipeli/projects-conf/local.conf conf/local.conf
   ```

   *(Optional)* If you prefer your `build/conf/` settings to dynamically mirror repository updates, you can create symlinks instead:

   ```bash
   ln -sf ../../meta-ledipeli/projects-conf/bblayers.conf conf/bblayers.conf
   ln -sf ../../meta-ledipeli/projects-conf/local.conf conf/local.conf
   ```

---

## 4. Building the Image

After copying or symlinking the configuration files, trigger the build process using BitBake:

```bash
bitbake ledipeli-image
```


---

## 5. Deployment

Once the build finishes successfully, images and bootable artifacts will be generated at:

```bash
build/tmp/deploy/images/
```

To copy the built image to an SD card (replace `/dev/sdX` with your card device identifier):

```bash
sudo dd if=tmp/deploy/images/<MACHINE>/core-image-minimal-<MACHINE>.wic status=progress conv=fsync of=/dev/sdX
```
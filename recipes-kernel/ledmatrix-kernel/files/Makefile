obj-m += ledmatrix.o
ledmatrix-y := src/ledmatrix.o

ccflags-y += -I$(src)/include

all: modules

modules:
	$(MAKE) -C $(KERNEL_SRC) M=$(CURDIR) modules

modules_install:
	$(MAKE) -C $(KERNEL_SRC) M=$(CURDIR) modules_install

clean:
	$(MAKE) -C $(KERNEL_SRC) M=$(CURDIR) clean

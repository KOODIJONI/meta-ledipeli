CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=199309L -DDEBUG_MATRIX
CFLAGS += -I./include -I./lib/cJSON


TARGET = build/matrix_test

SRCS = tests/main.c \
       src/matrix.c \
       src/args.c \
       src/config.c \
       src/buffer.c \
       src/color.c \
       lib/cJSON/cJSON.c

OBJS = $(patsubst %.c,build/%.o,$(SRCS))

HEADERS = $(wildcard include/*.h)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

build/%.o: %.c $(HEADERS)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -rf build

.PHONY: all clean run

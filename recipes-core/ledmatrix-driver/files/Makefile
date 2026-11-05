CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -DDEBUG_MATRIX

TARGET = matrix_test
SRCS = main.c matrix.c args.c
OBJS = $(SRCS:.c=.o)
HEADERS = matrix.h color.h args.h

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean run

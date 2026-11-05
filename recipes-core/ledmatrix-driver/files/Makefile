CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -DDEBUG_MATRIX

TARGET = matrix_test
CFLAGS += -I./lib/cJSON
SRCS = main.c matrix.c args.c config.c buffer.c lib/cJSON/cJSON.c 
OBJS = $(SRCS:.c=.o)
HEADERS = matrix.h color.h args.h buffer.h

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

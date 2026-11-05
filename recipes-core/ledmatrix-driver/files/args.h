#ifndef ARGS_H
#define ARGS_H
#include <stdint.h>
#include <stdbool.h>
#include "matrix.h"

int parse_args(int argc, char *argv[], MatrixConfig *config);


#endif // ARGS_H
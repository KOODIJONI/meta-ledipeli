#include <stdio.h>
#include <stdint.h>
#include "matrix.c"


int main(){
    
    printf("Hello World :D\n");
    initMatrix();
    write_color(&matrix[2][1],255,255,255);
    write_rectFill(1,1,22,22,255,255,255);
    printMatrix();
    return 0;
}


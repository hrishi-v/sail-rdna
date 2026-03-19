#include "kernel.h"
#ifndef TEST_INC
#define TEST_INC "../asm/add_one.inc"
#endif

extern "C" __global__
void asm_kernel(int* out) {
    int result = 0;

    asm volatile(
        #include TEST_INC
        : "=v"(result)
        :
        : "v5", "v6", "memory"
    );

    *out = result;
}

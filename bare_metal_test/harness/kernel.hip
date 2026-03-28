#include "kernel.h"

#ifndef TEST_INC
#define TEST_INC "../asm/add_one.inc"
#endif

#ifndef DUMP_INC
#define DUMP_INC "../asm/add_one_dump.inc"
#endif

extern "C" __global__
void asm_kernel(int* vgpr_out, int* sgpr_out) {
    asm volatile(
        #include TEST_INC
        #include DUMP_INC
    );
}
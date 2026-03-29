#include "kernel.h"
#include <stdint.h>

#ifndef TEST_INC
#define TEST_INC "../asm/add_one.inc"
#endif

#ifndef DUMP_INC
#define DUMP_INC "../asm/add_one_dump.inc"
#endif

extern "C" __global__
void asm_kernel(int* vgpr_out, int* sgpr_out) {
    // Compute per-lane store address in HIP so the asm doesn't need to.
    // addr_lo/addr_hi are passed as "v" inputs (%0 and %1).
    // v2 and v3 are in the clobber list so the compiler won't alias them with %0/%1.
    uint64_t addr = (uint64_t)(vgpr_out + threadIdx.x);
    uint32_t addr_lo = (uint32_t)(addr);
    uint32_t addr_hi = (uint32_t)(addr >> 32);
    asm volatile(
        #include TEST_INC
        #include DUMP_INC
        :
        : "v"(addr_lo), "v"(addr_hi)
        : "v0", "v1", "v2", "v3", "v5", "v6", "memory"
    );
}

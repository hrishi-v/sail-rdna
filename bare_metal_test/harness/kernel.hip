#include "kernel.h"
#include <stdint.h>

#ifndef TEST_INC
#define TEST_INC "../asm/add_one.inc"
#endif

#ifndef DUMP_INC
#define DUMP_INC "../asm/add_one_dump.inc"
#endif

extern "C" __global__
void asm_kernel(int* vgpr_out, int* sgpr_out, int* mem_buf) {
    // %0/%1: per-lane vgpr_out address (lo/hi), used by all dump files
    uint64_t addr = (uint64_t)(vgpr_out + threadIdx.x);
    uint32_t addr_lo = (uint32_t)(addr);
    uint32_t addr_hi = (uint32_t)(addr >> 32);
    // %2/%3: uniform mem_buf base address (lo/hi), used by memory tests
    uint64_t mem_buf_addr = (uint64_t)(mem_buf);
    uint32_t mem_buf_lo = (uint32_t)(mem_buf_addr);
    uint32_t mem_buf_hi = (uint32_t)(mem_buf_addr >> 32);
    asm volatile(
        #include TEST_INC
        #include DUMP_INCa
        :
        : "v"(addr_lo), "v"(addr_hi), "v"(mem_buf_lo), "v"(mem_buf_hi) // %0-3
        : "v0", "v1", "v2", "v3", "v4", "v5", "v6",
          "v10", "v11", "v12", "v13", "v14", "v15", "memory"
    );
}

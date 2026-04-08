#include <hip/hip_runtime.h>

extern "C" __global__ void exec_test(int* vgpr_dump, int* sgpr_dump, int* mem_buf) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    uint32_t result = 0;

    __asm__ volatile (
        "v_mov_b32 v1, 0xAAAAAAAA\n\t"
        "s_mov_b32 exec_lo, 0x2\n\t"       // Mask for Lane 1
        "s_waitcnt lgkmcnt(0)\n\t"
        "v_mov_b32 v1, 0xBBBBBBBB\n\t"    // Only Lane 1 should change
        "s_mov_b32 exec_lo, 0xFFFFFFFF\n\t" // Restore
        "s_waitcnt lgkmcnt(0)\n\t"
        "v_mov_b32 %[out], v1\n\t"         // All lanes should now show 0xAAAA except Lane 1
        : [out] "=v" (result)
        : "s"(vgpr_dump), "s"(sgpr_dump), "s"(mem_buf) 
        : "v1", "memory"
    );

    vgpr_dump[tid] = (int)result;
}
#include <hip/hip_runtime.h>

extern "C" __global__ void read_modify_write(int* vgpr_dump, int* sgpr_dump, int* mem_buf) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    __asm__ volatile("; BEGIN");
    int mem_val = mem_buf[0];
    int result = mem_val + tid + 100;
    __asm__ volatile("v_mov_b32 v5, %0" :: "v"(result) : "v5");
    __asm__ volatile("; END");
    vgpr_dump[tid] = result;
}

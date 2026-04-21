#include <hip/hip_runtime.h>

extern "C" __global__ void add_one(int* out, int* sgpr_dump, int* in) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    __asm__ volatile("; BEGIN");
    int x = in[tid] + 1;
    __asm__ volatile("v_mov_b32 v5, %0" :: "v"(x) : "v5");
    __asm__ volatile("; END");
    out[tid] = x;
}

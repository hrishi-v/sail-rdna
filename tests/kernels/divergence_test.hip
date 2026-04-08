#include <hip/hip_runtime.h>

extern "C" __global__ void divergence_test(int* vgpr_dump, int* sgpr_dump, int* mem_buf) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    int result;
    if (tid < 16) {
        result = 0xAAAAAAAA;
    } else {
        result = 0xBBBBBBBB;
    }
    vgpr_dump[tid] = result;
}
#include <hip/hip_runtime.h>

extern "C" __global__ void read_modify_write(int* vgpr_dump, int* sgpr_dump, int* mem_buf) {
    int tid = threadIdx.x;
    int val = mem_buf[tid];
    int result = (val * 2) + 100;
    mem_buf[tid] = result;
    
    vgpr_dump[tid] = result;
}
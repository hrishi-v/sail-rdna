#include <hip/hip_runtime.h>

extern "C" __global__ void read_modify_write(int* vgpr_dump, int* sgpr_dump, int* mem_buf) {
    int tid = threadIdx.x;
    int result = (tid * 2) + 100;

    asm volatile("// DUMP_HOOK"); 
    
    vgpr_dump[tid] = result;
}
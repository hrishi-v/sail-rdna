#pragma once
#include <hip/hip_runtime.h>

extern "C" __global__
void asm_kernel(int* vgpr_out, int* sgpr_out, int* mem_buf);

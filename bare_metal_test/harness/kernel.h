#pragma once
#include <hip/hip_runtime.h>

extern "C" __global__
void asm_kernel(int* out);

#include <hip/hip_runtime.h>

__global__ void add(int* out, int* a, int* b) {
    out[0] = a[0] + b[0];
}

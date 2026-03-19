#include <hip/hip_runtime.h>
#include <iostream>
#include "kernel.h"

#define CHECK(x) do { auto err = (x); if (err != hipSuccess) { \
  std::cerr << hipGetErrorString(err) << "\n"; std::exit(1); } } while(0)


int main() {
    int *d_out;
    int h_out = 0;

    CHECK(hipMalloc(&d_out, sizeof(int)));

    hipLaunchKernelGGL(
        asm_kernel,
        dim3(1), dim3(1),
        0, 0,
        d_out
    );

    CHECK(hipGetLastError());
    CHECK(hipDeviceSynchronize());

    CHECK(hipMemcpy(&h_out, d_out, sizeof(int), hipMemcpyDeviceToHost));
    CHECK(hipFree(d_out));

    std::cout << "Result: " << h_out << "\n";
}

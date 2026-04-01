#include <hip/hip_runtime.h>
#include <iostream>
#include <cstdlib>

#define CHECK(x) do { \
    auto err = (x); \
    if (err != hipSuccess) { \
        std::cerr << "HIP error: " << hipGetErrorString(err) << "\n"; \
        std::exit(1); \
    } \
} while (0)

// Kernel: each thread reads arr[i], adds val, writes arr[i] back.
//
// Compiler output typically contains:
//   s_load_b64          -- load kernel args (arr pointer)
//   v_lshlrev_b32       -- threadIdx.x * 4  (byte offset)
//   v_add_co_u32        -- base + offset (low 32 bits of address)
//   v_addc_co_u32       -- carry into high 32 bits
//   global_load_b32     -- load arr[i]
//   s_waitcnt vmcnt(0)  -- wait for load
//   v_add_nc_u32        -- add val
//   global_store_b32    -- store arr[i]


__global__ void read_modify_write(int* arr, int val) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    arr[i] = arr[i] + val;
}

int main() {
    const int N = 32;
    const int VAL = 10;

    int h_in[N], h_out[N];
    for (int i = 0; i < N; i++) h_in[i] = i;

    int* d_arr;
    CHECK(hipMalloc(&d_arr, N * sizeof(int)));
    CHECK(hipMemcpy(d_arr, h_in, N * sizeof(int), hipMemcpyHostToDevice));

    read_modify_write<<<dim3(1), dim3(N)>>>(d_arr, VAL);

    CHECK(hipGetLastError());
    CHECK(hipDeviceSynchronize());

    CHECK(hipMemcpy(h_out, d_arr, N * sizeof(int), hipMemcpyDeviceToHost));
    CHECK(hipFree(d_arr));

    int failures = 0;
    for (int i = 0; i < N; i++) {
        int expected = h_in[i] + VAL;
        if (h_out[i] != expected) {
            std::cerr << "FAIL  lane " << i
                      << "  expected " << expected
                      << "  got " << h_out[i] << "\n";
            failures++;
        }
    }

    if (failures == 0)
        std::cout << "PASS  read_modify_write  (N=" << N << " val=" << VAL << ")\n";

    return failures > 0 ? 1 : 0;
}

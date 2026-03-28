#include <hip/hip_runtime.h>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <cstring>
#include <sys/stat.h>
#include "kernel.h"

#ifndef NUM_VGPRS
#define NUM_VGPRS 16
#endif

#ifndef NUM_SGPRS
#define NUM_SGPRS 0
#endif

#ifndef TEST_NAME
#define TEST_NAME "add_one"
#endif

#define CHECK(x) do { auto err = (x); if (err != hipSuccess) { \
  std::cerr << hipGetErrorString(err) << "\n"; std::exit(1); } } while(0)

static void write_register_file(const char* path, const char* prefix,
                                const int* values, int count,
                                const int* indices) {
    std::ofstream f(path);
    if (!f) {
        std::cerr << "Failed to open " << path << "\n";
        std::exit(1);
    }
    for (int i = 0; i < count; i++) {
        f << prefix << indices[i] << " = 0x"
          << std::hex << std::setfill('0') << std::setw(8)
          << static_cast<unsigned>(values[i]) << "\n";
    }
}

#ifndef VGPR_INDICES
#define VGPR_INDICES {5}
#endif

#ifndef SGPR_INDICES
#define SGPR_INDICES {}
#endif

int main() {
    int *d_vgpr, *d_sgpr;
    int h_vgpr[NUM_VGPRS] = {};
    int h_sgpr[NUM_SGPRS > 0 ? NUM_SGPRS : 1] = {};

    CHECK(hipMalloc(&d_vgpr, NUM_VGPRS * sizeof(int)));
    CHECK(hipMalloc(&d_sgpr, (NUM_SGPRS > 0 ? NUM_SGPRS : 1) * sizeof(int)));
    CHECK(hipMemset(d_vgpr, 0, NUM_VGPRS * sizeof(int)));
    CHECK(hipMemset(d_sgpr, 0, (NUM_SGPRS > 0 ? NUM_SGPRS : 1) * sizeof(int)));

    hipLaunchKernelGGL(
        asm_kernel,
        dim3(1), dim3(1),
        0, 0,
        d_vgpr, d_sgpr
    );

    CHECK(hipGetLastError());
    CHECK(hipDeviceSynchronize());

    CHECK(hipMemcpy(h_vgpr, d_vgpr, NUM_VGPRS * sizeof(int), hipMemcpyDeviceToHost));
    if (NUM_SGPRS > 0)
        CHECK(hipMemcpy(h_sgpr, d_sgpr, NUM_SGPRS * sizeof(int), hipMemcpyDeviceToHost));

    CHECK(hipFree(d_vgpr));
    CHECK(hipFree(d_sgpr));

    mkdir("outputs", 0755);

    const int vgpr_indices[] = VGPR_INDICES;
    write_register_file(
        "outputs/" TEST_NAME "_vector_registers", "v",
        h_vgpr, NUM_VGPRS, vgpr_indices
    );

    if (NUM_SGPRS > 0) {
        const int sgpr_indices[] = SGPR_INDICES;
        write_register_file(
            "outputs/" TEST_NAME "_scalar_registers", "s",
            h_sgpr, NUM_SGPRS, sgpr_indices
        );
    }

    std::cout << "=== " TEST_NAME " register dump ===" << "\n";
    const int* vi = vgpr_indices;
    for (int i = 0; i < NUM_VGPRS; i++)
        std::cout << "v" << vi[i] << " = 0x"
                  << std::hex << std::setfill('0') << std::setw(8)
                  << static_cast<unsigned>(h_vgpr[i]) << "\n";
    for (int i = 0; i < NUM_SGPRS; i++) {
        const int* si = (const int[])SGPR_INDICES;
        std::cout << "s" << si[i] << " = 0x"
                  << std::hex << std::setfill('0') << std::setw(8)
                  << static_cast<unsigned>(h_sgpr[i]) << "\n";
    }
}
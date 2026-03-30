#include <hip/hip_runtime.h>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <cstring>
#include <sys/stat.h>
#include "kernel.h"
#include "constants.h"

// Prefix used when writing captured register names to the output file.
// Override at compile time with -DCAPTURE_PREFIX='"s"' for scalar captures.
#ifndef CAPTURE_PREFIX
#define CAPTURE_PREFIX "v"
#endif

#define CHECK(x) do { auto err = (x); if (err != hipSuccess) { \
  std::cerr << hipGetErrorString(err) << "\n"; std::exit(1); } } while(0)

// Writes one line per register: "v5: lane0 lane1 ... lane31"
// values is laid out as [reg0_lane0 .. reg0_lane31, reg1_lane0 .. reg1_lane31, ...]
static void write_register_file(const char* path, const char* prefix,
                                const int* values, int num_regs,
                                const int* indices) {
    std::ofstream f(path);
    if (!f) {
        std::cerr << "Failed to open " << path << "\n";
        std::exit(1);
    }
    for (int i = 0; i < num_regs; i++) {
        f << prefix << indices[i] << ":";
        for (int lane = 0; lane < WAVE_SIZE; lane++) {
            f << " " << std::hex << std::setfill('0') << std::setw(8)
              << static_cast<unsigned>(values[i * WAVE_SIZE + lane]);
        }
        f << "\n";
    }
}

int main() {
    int *d_vgpr, *d_sgpr, *d_mem_buf;
    int h_vgpr[NUM_VGPRS * WAVE_SIZE] = {};
    int h_sgpr[NUM_SGPRS > 0 ? NUM_SGPRS : 1] = {};

    CHECK(hipMalloc(&d_vgpr, NUM_VGPRS * WAVE_SIZE * sizeof(int)));
    CHECK(hipMalloc(&d_sgpr, (NUM_SGPRS > 0 ? NUM_SGPRS : 1) * sizeof(int)));
    CHECK(hipMalloc(&d_mem_buf, MEM_BUF_SIZE * sizeof(int)));
    CHECK(hipMemset(d_vgpr, 0, NUM_VGPRS * WAVE_SIZE * sizeof(int)));
    CHECK(hipMemset(d_sgpr, 0, (NUM_SGPRS > 0 ? NUM_SGPRS : 1) * sizeof(int)));
    CHECK(hipMemset(d_mem_buf, 0, MEM_BUF_SIZE * sizeof(int)));

    hipLaunchKernelGGL(
        asm_kernel,
        dim3(1), dim3(WAVE_SIZE),
        0, 0,
        d_vgpr, d_sgpr, d_mem_buf
    );

    CHECK(hipGetLastError());
    CHECK(hipDeviceSynchronize());

    CHECK(hipMemcpy(h_vgpr, d_vgpr, NUM_VGPRS * WAVE_SIZE * sizeof(int), hipMemcpyDeviceToHost));
    if (NUM_SGPRS > 0)
        CHECK(hipMemcpy(h_sgpr, d_sgpr, NUM_SGPRS * sizeof(int), hipMemcpyDeviceToHost));

    CHECK(hipFree(d_vgpr));
    CHECK(hipFree(d_sgpr));
    CHECK(hipFree(d_mem_buf));

    mkdir("outputs", 0755);

    const int vgpr_indices[] = VGPR_INDICES;
    write_register_file(
        "outputs/" TEST_NAME "_vector_registers", CAPTURE_PREFIX,
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
    for (int i = 0; i < NUM_VGPRS; i++) {
        std::cout << CAPTURE_PREFIX << std::dec << vi[i] << ":";
        for (int lane = 0; lane < WAVE_SIZE; lane++)
            std::cout << " " << std::hex << std::setfill('0') << std::setw(8)
                      << static_cast<unsigned>(h_vgpr[i * WAVE_SIZE + lane]);
        std::cout << "\n";
    }
    if (NUM_SGPRS > 0) {
        const int sgpr_indices[] = SGPR_INDICES;
        for (int i = 0; i < NUM_SGPRS; i++)
            std::cout << "s" << std::dec << sgpr_indices[i] << ": "
                      << std::hex << std::setfill('0') << std::setw(8)
                      << static_cast<unsigned>(h_sgpr[i]) << "\n";
    }
}
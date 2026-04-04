#include <hip/hip_runtime.h>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <cstring>
#include <sys/stat.h>
#include <vector>
#include <string>

// Hide the JSON library ONLY during the GPU pass
#if !defined(__HIP_DEVICE_COMPILE__)
#include <nlohmann/json.hpp>
using json = nlohmann::json;
#endif

#ifndef OUTPUT_DIR
#define OUTPUT_DIR "outputs"
#endif

// Essential Constants
static constexpr int WAVE_SIZE   = 32;
static constexpr int MEM_BUF_INT = 64; 

// Error Checking Macros
#define CHECK_HIP(x) do { \
    hipError_t _err = (x); \
    if (_err != hipSuccess) { \
        std::cerr << "HIP error at " << __FILE__ << ":" << __LINE__ \
                  << " - " << hipGetErrorString(_err) << "\n"; \
        std::exit(1); \
    } \
} while(0)

#define CHECK_MOD(x) CHECK_HIP(x)

static void write_register_file(const std::string& path,
                                const std::string& prefix,
                                const std::vector<int>& values,
                                const std::vector<int>& indices) {
    std::ofstream f(path);
    if (!f) {
        std::cerr << "Failed to open " << path << "\n";
        std::exit(1);
    }
    int num_regs = static_cast<int>(indices.size());
    for (int i = 0; i < num_regs; i++) {
        f << prefix << indices[i] << ":";
        for (int lane = 0; lane < WAVE_SIZE; lane++) {
            f << " " << std::hex << std::setfill('0') << std::setw(8)
              << static_cast<unsigned>(values[i * WAVE_SIZE + lane]);
        }
        f << "\n";
    }
}

static void dump_registers_stdout(const std::string& test_name,
                                  const std::string& prefix,
                                  const std::vector<int>& values,
                                  const std::vector<int>& indices) {
    std::cout << "=== " << test_name << " register dump ===\n";
    int num_regs = static_cast<int>(indices.size());
    for (int i = 0; i < num_regs; i++) {
        std::cout << prefix << std::dec << indices[i] << ":";
        for (int lane = 0; lane < WAVE_SIZE; lane++) {
            std::cout << " " << std::hex << std::setfill('0') << std::setw(8)
                      << static_cast<unsigned>(values[i * WAVE_SIZE + lane]);
        }
        std::cout << "\n";
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: harness <manifest.json>\n";
        return 1;
    }

#if !defined(__HIP_DEVICE_COMPILE__)
    json manifest;
    {
        std::ifstream f(argv[1]);
        if (!f) {
            std::cerr << "Cannot open manifest: " << argv[1] << "\n";
            return 1;
        }
        f >> manifest;
    }

    const std::string test_name      = manifest["name"].get<std::string>();
    const std::string capture_prefix = manifest.value("capture_prefix", "v");
    const std::string kernel_name    = manifest.value("kernel_name", "asm_kernel");
    
    std::string binary_path;
    if (manifest.contains("binary_path")) {
        binary_path = manifest["binary_path"].get<std::string>();
    } else {
        binary_path = "bare_metal_test/outputs/binaries/" + test_name + ".co";
    }

    const int num_vgprs = manifest["registers"]["vgprs"]["count"].get<int>();
    const int num_sgprs = manifest["registers"]["sgprs"]["count"].get<int>();
    std::vector<int> vgpr_indices = manifest["registers"]["vgprs"]["indices"].get<std::vector<int>>();
    std::vector<int> sgpr_indices = manifest["registers"]["sgprs"]["indices"].get<std::vector<int>>();

    const int vgpr_elems = num_vgprs * WAVE_SIZE;
    const int sgpr_elems = (num_sgprs > 0) ? num_sgprs : 1;

    std::vector<int> h_mem_buf(MEM_BUF_INT, 0);
    if (manifest.contains("initial_memory_hex")) {
        auto hex_strs = manifest["initial_memory_hex"].get<std::vector<std::string>>();
        for (size_t i = 0; i < hex_strs.size() && i < MEM_BUF_INT; i++) {
            h_mem_buf[i] = static_cast<int>(std::stoul(hex_strs[i], nullptr, 16));
        }
    }

    int *d_vgpr, *d_sgpr, *d_mem_buf;
    CHECK_HIP(hipMalloc(&d_vgpr,    vgpr_elems * sizeof(int)));
    CHECK_HIP(hipMalloc(&d_sgpr,    sgpr_elems * sizeof(int)));
    CHECK_HIP(hipMalloc(&d_mem_buf, MEM_BUF_INT * sizeof(int)));
    
    CHECK_HIP(hipMemset(d_vgpr,    0, vgpr_elems * sizeof(int)));
    CHECK_HIP(hipMemset(d_sgpr,    0, sgpr_elems * sizeof(int)));
    CHECK_HIP(hipMemcpy(d_mem_buf, h_mem_buf.data(), MEM_BUF_INT * sizeof(int), hipMemcpyHostToDevice));

    hipModule_t   module;
    hipFunction_t kernel_fn;
    CHECK_MOD(hipModuleLoad(&module, binary_path.c_str()));
    CHECK_MOD(hipModuleGetFunction(&kernel_fn, module, kernel_name.c_str()));

    void* args[] = { &d_vgpr, &d_sgpr, &d_mem_buf };
    CHECK_MOD(hipModuleLaunchKernel(
        kernel_fn,
        1, 1, 1,           
        WAVE_SIZE, 1, 1,   
        0, nullptr, args, nullptr
    ));

    CHECK_HIP(hipDeviceSynchronize());

    std::vector<int> h_vgpr(vgpr_elems, 0);
    std::vector<int> h_sgpr(sgpr_elems, 0);

    CHECK_HIP(hipMemcpy(h_vgpr.data(), d_vgpr, vgpr_elems * sizeof(int), hipMemcpyDeviceToHost));
    if (num_sgprs > 0)
        CHECK_HIP(hipMemcpy(h_sgpr.data(), d_sgpr, num_sgprs * sizeof(int), hipMemcpyDeviceToHost));

    CHECK_HIP(hipFree(d_vgpr));
    CHECK_HIP(hipFree(d_sgpr));
    CHECK_HIP(hipFree(d_mem_buf));
    CHECK_MOD(hipModuleUnload(module));

    mkdir(OUTPUT_DIR, 0755);
    write_register_file(std::string(OUTPUT_DIR) + "/" + test_name + "_vector_registers", capture_prefix, h_vgpr, vgpr_indices);
    if (num_sgprs > 0) write_register_file(std::string(OUTPUT_DIR) + "/" + test_name + "_scalar_registers", "s", h_sgpr, sgpr_indices);

    dump_registers_stdout(test_name, capture_prefix, h_vgpr, vgpr_indices);
    if (num_sgprs > 0) dump_registers_stdout(test_name + " (scalar)", "s", h_sgpr, sgpr_indices);

#endif
    return 0;
}
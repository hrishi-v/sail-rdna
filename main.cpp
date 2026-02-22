#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>

#include <gmp.h> 

extern "C" {
    #include "sail.h"
    #include "out.h" 
    
    void model_init(void);
    unit zsail_test_main(unit);
    unit zwrite_mem_8(uint64_t addr, uint64_t data);
    unit zset_pc(uint64_t start_addr);
    bool zget_halt_flag(unit);
    unit zstep(unit);
}

int main(int argc, char** argv) {
    model_init(); 

    if (argc < 2) {
        std::cout << "[Emulator] No binary provided. Booting internal test suite...\n";
        zsail_test_main(UNIT);
        return 0;
    }

    std::cout << "[Emulator] Loading kernel: " << argv[1] << "\n";
    std::ifstream file(argv[1], std::ios::binary);
    if (!file) {
        std::cerr << "Error: Could not open file.\n";
        return 1;
    }
    std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    uint64_t base_address = 0x0100;
    for (size_t i = 0; i < buffer.size(); i++) {
        zwrite_mem_8((uint64_t)(base_address + i), (uint64_t)buffer[i]); 
    }

    std::cout << "[Emulator] Kernel flashed. Booting Wavefront...\n";
    zset_pc(base_address);
    
    int cycle_count = 0;
    while (!zget_halt_flag(UNIT)) {
        zstep(UNIT);
        cycle_count++;
        
        if (cycle_count > 10000) {
            std::cerr << "[Emulator] ERROR: Hit 10,000 cycles. Forcing exit.\n";
            return 1;
        }
    }

    std::cout << "[Emulator] Execution complete. Cycles: " << cycle_count << "\n";
    return 0;
}
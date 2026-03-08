#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <iomanip>
#include <filesystem>
#include <string>

#include <gmp.h> 

extern "C" {
    #include "sail.h"
    #include "out.h" 
    #include "elf.h"

    extern uint64_t zVMCNT;
    extern uint64_t zLGKMCNT;
    extern uint64_t zEXEC_LO;
    extern uint64_t zSHARED_BASE;
    
    void model_init(void);
    unit zsail_test_main(unit); 
    unit zwrite_mem_8(uint64_t addr, uint64_t data);
    unit zwSGPR(uint64_t reg, uint64_t data); 
    
    unit zset_pc(uint64_t start_addr);
    bool zget_halt_flag(unit);
    unit zstep(unit);

    uint64_t zrVGPR(uint64_t reg, uint64_t lane);
    uint64_t zread_scalar_source(uint64_t reg);
}

void dump_gpu_state() {
    std::cout << "[Emulator] Generating state dump in outputs/...\n";

    std::filesystem::create_directory("outputs");
    std::ofstream sys_log("outputs/system.log");

    sys_log << "--- SYSTEM STATE ---\n";
    sys_log << "EXEC_LO: 0x" << std::hex << zEXEC_LO << "\n";
    sys_log << "VMCNT:   " << std::dec << zVMCNT << "\n";
    sys_log << "LGKMCNT: " << std::dec << zLGKMCNT << "\n";
    sys_log.close();

    std::ofstream sgpr_log("outputs/sgpr.log");
    sgpr_log << "--- SCALAR REGISTERS (SGPR) ---\n";
    for (int i = 0; i < 106; i++) {
        uint64_t val = zread_scalar_source(i);
        if (val != 0) {
            sgpr_log << "SGPR[" << std::dec << i << "]: 0x" << std::hex << std::setw(8) << std::setfill('0') << val << "\n";
        }
    }
    sgpr_log.close();

    std::ofstream vgpr_log("outputs/vgpr.log");
    vgpr_log << "--- VECTOR REGISTERS (VGPR) ---\n";
    for (int reg = 0; reg < 256; reg++) {
        bool has_data = false;
        std::stringstream lane_data;
        
        for (int lane = 0; lane < 32; lane++) {
            uint64_t val = zrVGPR(reg, lane);
            if (val != 0) {
                has_data = true;
                lane_data << "  L" << std::dec << lane << ": 0x" << std::hex << val;
            }
        }
        if (has_data) {
            vgpr_log << "VGPR[" << std::dec << reg << "]\n" << lane_data.str() << "\n\n";
        }
    }
    vgpr_log.close();
    
    std::ofstream mem_log("outputs/memory.log");
    mem_log << "--- MEMORY DUMP (Target Regions) ---\n";
    
    mem_log << "\n[Aperture: Shared/LDS]\n";
    for (uint64_t addr = 0x1000; addr <= 0x1020; addr += 4) {
        uint64_t val = zread_mem_32(addr); // Changed from uint32_t
        mem_log << "0x" << std::hex << addr << ": 0x" << std::setw(8) << std::setfill('0') << val << "\n";
    }

    mem_log << "\n[Aperture: Global/VRAM]\n";
    for (uint64_t addr = 0x2000; addr <= 0x2020; addr += 4) {
        uint64_t val = zread_mem_32(addr); // Changed from uint32_t
        mem_log << "0x" << std::hex << addr << ": 0x" << std::setw(8) << std::setfill('0') << val << "\n";
    }
    
    mem_log.close();
    std::cout << "[Emulator] State dump complete.\n";
}

int main(int argc, char** argv) {
    model_init(); 

    if (argc < 2) {
        std::cout << "[Emulator] No binary provided. Booting internal test suite...\n";
        zsail_test_main(UNIT); 
        return 0;
    }

    std::string filename = argv[1];
    uint64_t entry_pc = 0x0100;

    if (filename.find(".elf") != std::string::npos) {
        std::cout << "[Emulator] Loading ELF kernel: " << filename << "\n";
        bool is32bit = false;
        
        uint64_t ptr_C = 0x00002000;
        uint64_t ptr_A = 0x00003000;
        uint64_t ptr_B = 0x00004000;
        zwrite_mem_32(ptr_A, 10); 
        zwrite_mem_32(ptr_B, 20); 

        uint64_t kernarg_base = 0x00001000;
        zwrite_mem_32(kernarg_base + 0, ptr_C);
        zwrite_mem_32(kernarg_base + 4, 0x00000000); 

        zwrite_mem_32(kernarg_base + 8, ptr_A);
        zwrite_mem_32(kernarg_base + 12, 0x00000000);

        zwrite_mem_32(kernarg_base + 16, ptr_B);
        zwrite_mem_32(kernarg_base + 20, 0x00000000);

        zwSGPR(4, kernarg_base & 0xFFFFFFFF); 
        zwSGPR(5, (kernarg_base >> 32) & 0xFFFFFFFF);

        std::cout << "[Emulator] ELF flashed. Entry PC: 0x" << std::hex << entry_pc << "\n";
    } 
    else {
        std::cout << "[Emulator] Loading raw binary: " << filename << "\n";
        std::ifstream file(filename, std::ios::binary);
        if (!file) {
            std::cerr << "Error: Could not open file.\n";
            return 1;
        }
        std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

        for (size_t i = 0; i < buffer.size(); i++) {
            zwrite_mem_8(entry_pc + i, buffer[i]); 
        }
        std::cout << "[Emulator] Binary flashed.\n";
    }

    std::cout << "[Emulator] Booting Wavefront at PC: 0x" << std::hex << entry_pc << "\n";
    zset_pc(entry_pc);
    
    int cycle_count = 0;
    while (!zget_halt_flag(UNIT)) {
        zstep(UNIT);
        cycle_count++;
        
        if (cycle_count > 10000) {
            std::cerr << "[Emulator] ERROR: Hit 10,000 cycles. Forcing exit.\n";
            dump_gpu_state();
            return 1;
        }
    }

    std::cout << "[Emulator] Execution cleanly halted. Cycles: " << std::dec << cycle_count << "\n";
    dump_gpu_state();

    return 0;
}
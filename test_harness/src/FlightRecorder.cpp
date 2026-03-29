#include "FlightRecorder.h"
#include "log.h"
#include <fstream>
#include <cstdio>
#include <bitset>
#include <iomanip>
#include <vector>
#include <string>
#include <map>

FlightRecorder::FlightRecorder() : mismatch_detected(false) {
    trace_log.reserve(10000);
}

void FlightRecorder::record_instruction_cycle(int cycle, uint64_t pc, uint32_t opcode) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
             "[Cycle %05d] PC: 0x%04llX | Inst: 0x%08X",
             cycle, (unsigned long long)pc, opcode);
    trace_log.push_back(std::string(buffer));
}

void FlightRecorder::flag_mismatch() {
    mismatch_detected = true;
}

void FlightRecorder::dump_trace(const std::string &filepath) {
    std::ofstream logfile(filepath);
    if (!logfile.is_open()) return;

    for (const auto &line : trace_log) {
        logfile << line << "\n";
    }
    logfile.close();
}

void FlightRecorder::dump_vector_registers(const std::string &filepath) {
    std::ofstream logfile(filepath);
    if (!logfile.is_open()) return;

    for (int i = 0; i < 256; i++) {
        logfile << "v" << std::dec << i << ": ";
        for (int lane = 0; lane < 32; lane++) {
            uint32_t val = zrVGPR(i, lane);
            logfile << "0x" << std::hex << std::setw(8) << std::setfill('0') << val << " ";
        }
        logfile << "\n";
    }
    logfile.close();
}

void FlightRecorder::dump_scalar_registers(const std::string &filepath) {
    std::ofstream logfile(filepath);
    if (!logfile.is_open()) return;

    for (int i = 0; i < 108; i++) {
        logfile << "s" << std::dec << i << ": ";
        uint32_t val = zget_sgpr(i);
        logfile << std::hex << std::setw(8) << std::setfill('0') << val << " ";
        logfile << "\n";
    }
    logfile.close();
}

// --- VCD LOGIC ---

void FlightRecorder::init_vcd(const std::string &filepath) {
    vcd_file.open(filepath);
    if (!vcd_file) {
        log_error("Recorder", "Failed to open VCD file: " + filepath);
        return;
    }
    vcd_file << "$date March 2026 $end\n";
    vcd_file << "$version Sail RDNA3 C-FFI Emulator $end\n";
    vcd_file << "$timescale 1ns $end\n";

    vcd_file << "$scope module gpu $end\n";
    vcd_file << "$var wire 64 p PC [63:0] $end\n";
    vcd_file << "$var wire 32 v v0_lane0 [31:0] $end\n";
    vcd_file << "$upscope $end\n";
    vcd_file << "$enddefinitions $end\n";
    vcd_file << "#0\n";
}

void FlightRecorder::record_vcd_step(int cycle, uint64_t pc, uint32_t v0) {
    if (!vcd_file.is_open()) return;
    vcd_file << "#" << (cycle * 10) << "\n";
    vcd_file << "b" << std::bitset<64>(pc) << " p\n";
    vcd_file << "b" << std::bitset<32>(v0) << " v\n";
}

void FlightRecorder::close_vcd() {
    if (vcd_file.is_open()) {
        vcd_file.close();
    }
}
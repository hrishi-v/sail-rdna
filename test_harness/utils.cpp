#include "utils.h"
#include "FlightRecorder.h"
#include "SailFFI.h"
#include "log.h"

#include <fstream>
#include <vector>
#include <string>
#include <filesystem>
#include <iterator>
#include <iomanip>
#include <sstream>

std::vector<std::string> get_test_files(const std::string& directory) {
    std::vector<std::string> test_files;
    if (!std::filesystem::exists(directory) || !std::filesystem::is_directory(directory)) {
        log_error("Test Suite", "Test directory not found: " + directory);
        return test_files;
    }

    for (const auto &entry : std::filesystem::directory_iterator(directory)) {
        if (entry.path().extension() == ".bin") {
            test_files.push_back(entry.path().string());
        }
    }
    return test_files;
}

bool load_binary_to_memory(const std::string &filepath, uint64_t start_pc) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file) {
        log_error("Loader", "Could not open binary: " + filepath);
        return false;
    }

    std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    for (size_t i = 0; i < buffer.size(); i++) {
        zwrite_mem_8(start_pc + i, buffer[i]);
    }

    std::ostringstream oss;
    oss << "Flashed 0x" << std::hex << buffer.size() << " bytes to PC 0x" << start_pc;
    log_info("Loader", oss.str());
    return true;
}

bool run_test(const std::string &filepath) {
    log_info("Test Suite", "========================================");
    log_info("Test Suite", "Running: " + filepath);
    log_info("Test Suite", "========================================");

    uint64_t start_pc = 0x0100;

    if (!load_binary_to_memory(filepath, start_pc)) {
        return false;
    }

    zset_pc(start_pc);

    FlightRecorder recorder;
    int cycle_count = 0;
    const int CYCLE_LIMIT = 10000;

    recorder.init_vcd("outputs/waveforms/trace.vcd");

    while (!zget_halt_flag(UNIT)) {
        uint64_t current_pc = zget_pc(UNIT);
        uint32_t current_inst = zread_mem_32(current_pc);
        uint32_t v0_val = zrVGPR(0, 0);

        recorder.record_vcd_step(cycle_count, current_pc, v0_val);
        recorder.record_instruction_cycle(cycle_count, current_pc, current_inst);

        zstep(UNIT);
        cycle_count++;

        if (cycle_count >= CYCLE_LIMIT) {
            log_error("Emulator", "Watchdog triggered for: " + filepath);
            recorder.flag_mismatch();
            break;
        }
    }

    std::filesystem::create_directories("outputs/instruction_trace");
    std::filesystem::create_directories("outputs/register_dumps");

    std::string base_name = std::filesystem::path(filepath).stem().string();
    std::string trace_log_path      = "outputs/instruction_trace/" + base_name + ".log";
    std::string vec_reg_dump_path   = "outputs/register_dumps/vec_" + base_name + ".log";
    std::string scal_reg_dump_path  = "outputs/register_dumps/scal_" + base_name + ".log";

    log_info("Recorder", "Writing execution trace to " + trace_log_path);
    recorder.dump_trace(trace_log_path);
    recorder.dump_vector_registers(vec_reg_dump_path);
    recorder.dump_scalar_registers(scal_reg_dump_path);

    bool timed_out   = (cycle_count >= CYCLE_LIMIT);
    bool error_hit   = zget_error_flag(UNIT);
    bool passed      = !timed_out && !error_hit;

    std::ostringstream result;
    result << filepath << " (" << std::dec << cycle_count << " cycles)";

    if (passed) {
        log_info("Test Suite", "PASS: " + result.str());
    } else if (timed_out) {
        log_warn("Test Suite", "FAIL (timeout): " + result.str());
    } else {
        log_warn("Test Suite", "FAIL (error): " + result.str());
    }

    return passed;
}

void reset_emulator_state() {
    zreset_halt_flag(UNIT);
    zreset_error_flag(UNIT);
    zreset_vmcnt(UNIT);
    zreset_lgkmcnt(UNIT);

    for (uint64_t i = 0; i < 65536; i++) {
        zwrite_mem_8(i, 0);
    }
    for (int i = 0; i < 108; i++) {
        zwSGPR(i, 0);
    }
    for (int i = 0; i < 256; i++) {
        for (int lane = 0; lane < 32; lane++) {
            zwVGPR(i, lane, 0);
        }
    }
}

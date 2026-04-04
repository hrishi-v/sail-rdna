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

// ---------------------------------------------------------------------------
// Kernel test support
// ---------------------------------------------------------------------------

namespace {

struct MemDump {
    uint64_t    addr;
    size_t      n_bytes;
    std::string path;
};

// Parse a numeric token that may be decimal or 0x-prefixed hex.
static uint64_t parse_uint(const std::string &s) {
    return std::stoull(s, nullptr, 0);
}

// Read the setup file and apply every directive to the Sail model.
// Returns the list of DUMP_MEM directives to execute after the kernel runs.
static std::vector<MemDump> apply_setup_file(const std::string &filepath) {
    std::vector<MemDump> dumps;
    std::ifstream f(filepath);
    if (!f) {
        log_error("KernelRunner", "Cannot open setup file: " + filepath);
        return dumps;
    }

    std::string line;
    while (std::getline(f, line)) {
        // Strip comments (everything from '#' onward).
        auto pos = line.find('#');
        if (pos != std::string::npos) line.resize(pos);

        std::istringstream iss(line);
        std::string directive;
        if (!(iss >> directive)) continue;

        if (directive == "SGPR") {
            std::string si, sv;
            iss >> si >> sv;
            zwSGPR(parse_uint(si), static_cast<uint32_t>(parse_uint(sv)));

        } else if (directive == "VGPR_LANE_ID") {
            std::string si;
            iss >> si;
            uint64_t idx = parse_uint(si);
            for (uint64_t lane = 0; lane < 32; lane++)
                zwVGPR(idx, lane, static_cast<uint32_t>(lane));

        } else if (directive == "VGPR_CONST") {
            std::string si, sv;
            iss >> si >> sv;
            uint64_t idx = parse_uint(si);
            uint32_t val = static_cast<uint32_t>(parse_uint(sv));
            for (uint64_t lane = 0; lane < 32; lane++)
                zwVGPR(idx, lane, val);

        } else if (directive == "MEM32") {
            std::string sa, sv;
            iss >> sa >> sv;
            zwrite_mem_32(parse_uint(sa), static_cast<uint32_t>(parse_uint(sv)));

        } else if (directive == "DUMP_MEM") {
            std::string sa, sn, sp;
            iss >> sa >> sn >> sp;
            dumps.push_back({parse_uint(sa), static_cast<size_t>(parse_uint(sn)), sp});
        }
    }
    return dumps;
}

} // namespace

bool run_kernel_test(const std::string &bin_path, const std::string &setup_path) {
    log_info("KernelRunner", "=== Kernel: " + bin_path + " ===");

    const uint64_t START_PC = 0x0100;
    if (!load_binary_to_memory(bin_path, START_PC)) return false;
    zset_pc(START_PC);

    // Apply initial register / memory state from the fixture-generated setup file.
    auto mem_dumps = apply_setup_file(setup_path);

    FlightRecorder recorder;
    int cycle = 0;
    const int CYCLE_LIMIT = 10000;

    while (!zget_halt_flag(UNIT)) {
        uint64_t pc   = zget_pc(UNIT);
        uint32_t inst = zread_mem_32(pc);
        recorder.record_instruction_cycle(cycle, pc, inst);
        zstep(UNIT);
        if (++cycle >= CYCLE_LIMIT) {
            log_error("KernelRunner", "Watchdog triggered for: " + bin_path);
            break;
        }
    }

    bool ok = (cycle < CYCLE_LIMIT) && !zget_error_flag(UNIT);

    // Write instruction trace (useful for debugging spec gaps).
    std::filesystem::create_directories("outputs/instruction_trace");
    std::string base = std::filesystem::path(bin_path).stem().string();
    recorder.dump_trace("outputs/instruction_trace/" + base + ".log");

    // Write each DUMP_MEM region.
    for (const auto &d : mem_dumps) {
        std::filesystem::create_directories(
            std::filesystem::path(d.path).parent_path());
        FlightRecorder::dump_memory_region(d.path, d.addr, d.n_bytes / 4);
    }

    log_info("KernelRunner", std::string(ok ? "PASS" : "FAIL") + ": " + bin_path);
    return ok;
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

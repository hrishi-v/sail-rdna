#include <vector>
#include <string>

#include <gmp.h>
#include "FlightRecorder.h"
#include "SailFFI.h"
#include "utils.h"
#include "log.h"

int main(int argc, char **argv)
{
    model_init();

    // Kernel test mode: rdna3_emu --kernel-test <bin> <setup>
    // Runs a single stripped kernel binary with the given setup file, then
    // dumps memory regions specified by DUMP_MEM directives in the setup.
    if (argc == 4 && std::string(argv[1]) == "--kernel-test") {
        reset_emulator_state();
        return run_kernel_test(argv[2], argv[3]) ? 0 : 1;
    }

    std::vector<std::string> tests_to_run;
    if (argc == 2) {
        tests_to_run.push_back(argv[1]);
    } else {
        tests_to_run = get_test_files("tests/bin");
    }

    if (tests_to_run.empty()) {
        log_warn("Test Suite", "No .bin files found.");
        return 1;
    }

    int passed = 0, total = 0;

    for (const auto& bin_path : tests_to_run) {
        total++;
        reset_emulator_state();

        if (run_test(bin_path)) {
            passed++;
        }
    }

    log_info("Test Suite", std::to_string(passed) + "/" + std::to_string(total) + " passed");
    return (passed == total) ? 0 : 1;
}

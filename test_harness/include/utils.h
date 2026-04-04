#pragma once

#include <vector>
#include "SailFFI.h"

std::vector<std::string> get_test_files(const std::string& directory);
bool load_binary_to_memory(const std::string &filepath, uint64_t start_pc);
bool run_test(const std::string &filepath);
bool run_kernel_test(const std::string &bin_path, const std::string &setup_path);
void reset_emulator_state();
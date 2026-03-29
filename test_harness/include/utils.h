#pragma once

#include <vector>
#include "SailFFI.h"

std::vector<std::string> get_test_files(const std::string& directory);
bool load_binary_to_memory(const std::string &filepath, uint64_t start_pc);
bool run_test(const std::string &filepath);
void reset_emulator_state();
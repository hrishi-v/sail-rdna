#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <filesystem>

#include <gmp.h> 
#include "FlightRecorder.h"
#include "SailFFI.h"

std::vector<std::string> get_test_files(const std::string& directory) {
    std::vector<std::string> test_files;
    if (!std::filesystem::exists(directory) || !std::filesystem::is_directory(directory))
    {
      std::cerr << "[Error] Test directory not found: " << directory << "\n";
      return test_files;
    }

    for (const auto &entry : std::filesystem::directory_iterator(directory))
    {
      if (entry.path().extension() == ".bin")
      {
        test_files.push_back(entry.path().string());
      }
    }
    return test_files;
}

bool load_binary_to_memory(const std::string &filepath, uint64_t start_pc)
{
  std::ifstream file(filepath, std::ios::binary);
  if (!file)
  {
    std::cerr << "[Error] Could not open binary: " << filepath << "\n";
    return false;
  }

  std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

  for (size_t i = 0; i < buffer.size(); i++)
  {
    zwrite_mem_8(start_pc + i, buffer[i]);
  }

  std::cout << "[Loader] Flashed " << buffer.size() << " bytes to PC 0x" << std::hex << start_pc << "\n";
  return true;
}

bool run_test(const std::string &filepath)
{
  std::cout << "\n========================================\n";
  std::cout << "[Test Suite] Running: " << filepath << "\n";
  std::cout << "========================================\n";

  uint64_t start_pc = 0x0100;

  if (!load_binary_to_memory(filepath, start_pc))
  {
    return false;
  }


  zset_pc(start_pc);

  FlightRecorder recorder;
  int cycle_count = 0;
  const int CYCLE_LIMIT = 10000;

  while (!zget_halt_flag(UNIT))
  {
    uint64_t current_pc = zget_pc(UNIT);
    uint32_t current_inst = zread_mem_32(current_pc);

    recorder.record_cycle(cycle_count, current_pc, current_inst);
    zstep(UNIT);
    cycle_count++;

    if (cycle_count >= CYCLE_LIMIT)
    {
      std::cerr << "[Emulator] Watchdog triggered!\n";
      recorder.flag_mismatch();
      break;
    }
  }

  std::filesystem::create_directory("outputs");

  std::string base_name = std::filesystem::path(filepath).filename().string();
  std::string log_name = "outputs/trace_" + base_name + ".log";
  recorder.dump_trace(log_name);

  bool passed = (cycle_count < CYCLE_LIMIT);
  if (passed)
  {
    std::cout << "[Test Suite] PASS: " << filepath << " (" << cycle_count << " cycles)\n";
  }
  else
  {
    std::cout << "[Test Suite] FAIL (Timeout): " << filepath << "\n";
  }

  return passed;

  return passed;
}

  void reset_emulator_state()
  {
    zreset_halt_flag(UNIT);
    zreset_vmcnt(UNIT);
    zreset_lgkmcnt(UNIT);
    for (uint64_t i = 0; i < 65536; i++)
    {
      zwrite_mem_8(i, 0);
    }
  }

  int main(int argc, char **argv)
  {
    model_init();
    std::vector<std::string> tests_to_run;

    if (argc == 2) {
      tests_to_run.push_back(argv[1]);
    } else {
      tests_to_run = get_test_files("tests/bin");
    }

    if (tests_to_run.empty())
    {
      std::cout << "[Test Suite] No .bin files found to execute.\n";
      return 1;
    }

    int passed_count = 0;
    for (const auto& test_file : tests_to_run) {
      reset_emulator_state();
      if (run_test(test_file))
      {
        passed_count++;
      }
    }

    return 0;
}
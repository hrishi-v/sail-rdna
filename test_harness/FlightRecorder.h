#pragma once

#include <vector>
#include <string>
#include <cstdint>

#include "SailFFI.h"

class FlightRecorder
{
private:
  std::vector<std::string> trace_log;
  bool mismatch_detected;

public:
  FlightRecorder();
  void record_instruction_cycle(int cycle, uint64_t pc, uint32_t opcode);
  void flag_mismatch();
  void dump_trace(const std::string &filepath);
  void dump_vector_registers(const std::string &filepath);

  // VCD Functions
  void record_vcd_step(int cycle, uint64_t pc, uint32_t v0);
  void init_vcd(const std::string &filepath);
};
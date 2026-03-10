#pragma once

#include <vector>
#include <string>
#include <cstdint>

class FlightRecorder
{
private:
  std::vector<std::string> trace_log;
  bool mismatch_detected;

public:
  FlightRecorder();
  void record_cycle(int cycle, uint64_t pc, uint32_t opcode);
  void flag_mismatch();
  void dump_trace(const std::string &filepath);
};
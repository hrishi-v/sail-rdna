#pragma once

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <cstdint>
#include <fstream>
#include <cstdio>
#include <bitset>  
#include <iomanip> 

#include "SailFFI.h"

class FlightRecorder
{
private:
  std::vector<std::string> trace_log;
  bool mismatch_detected;
  std::ofstream vcd_file;
  std::map<std::string, std::string> signal_map;

public:
  FlightRecorder();
  void record_instruction_cycle(int cycle, uint64_t pc, uint32_t opcode);
  void flag_mismatch();
  void dump_trace(const std::string &filepath);
  void dump_scalar_registers(const std::string &filepath);
  void dump_vector_registers(const std::string &filepath);

  // VCD Functions
  void record_vcd_step(int cycle, uint64_t pc, uint32_t v0);
  void init_vcd(const std::string &filepath);
  void close_vcd();
};
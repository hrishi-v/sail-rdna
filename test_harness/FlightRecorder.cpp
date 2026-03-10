#include "FlightRecorder.h"
#include <iostream>
#include <fstream>
#include <cstdio> // For snprintf

FlightRecorder::FlightRecorder() : mismatch_detected(false)
{
  trace_log.reserve(10000);
}

void FlightRecorder::record_cycle(int cycle, uint64_t pc, uint32_t opcode)
{
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "[Cycle %05d] PC: 0x%04llX | Inst: 0x%08X", cycle, pc, opcode);
  trace_log.push_back(std::string(buffer));
}

void FlightRecorder::flag_mismatch()
{
  mismatch_detected = true;
}

void FlightRecorder::dump_trace(const std::string &filepath)
{
  std::cout << "[Recorder] Writing execution trace to " << filepath << "...\n";
  std::ofstream logfile(filepath);

  if (!logfile.is_open())
  {
    std::cerr << "[Recorder Error] Could not open log file: " << filepath << "\n";
    std::cerr << "                 (Does the 'outputs/' directory exist?)\n";
    return;
  }

  for (const auto &line : trace_log)
  {
    logfile << line << "\n";
  }

  logfile.close();
}
#include "FlightRecorder.h"
#include <iostream>
#include <fstream>
#include <cstdio>
#include <fstream>

FlightRecorder::FlightRecorder() : mismatch_detected(false)
{
  trace_log.reserve(10000);
}


void FlightRecorder::init_vcd(const std::string &filepath)
{
  vcd_file.open(filepath);
  vcd_file << "$date " << "March 2026" << " $end\n";
  vcd_file << "$version Sail RDNA3 Emulator $end\n";
  vcd_file << "$timescale 1ns $end\n";

  vcd_file << "$scope module gpu $end\n";
  vcd_file << "$var wire 64 pc_sig PC [63:0] $end\n";
  vcd_file << "$var wire 32 v0_sig v0_lane0 [31:0] $end\n";
  vcd_file << "$upscope $end\n";
  vcd_file << "$enddefinitions $end\n";
}

void FlightRecorder::record_vcd_step(int cycle, uint64_t pc, uint32_t v0)
{
  vcd_file << "#" << cycle << "\n";
  vcd_file << "b" << std::bitset<64>(pc) << " pc_sig\n";
  vcd_file << "b" << std::bitset<32>(v0) << " v0_sig\n";
}

void FlightRecorder::record_instruction_cycle(int cycle, uint64_t pc, uint32_t opcode)
{
  char buffer[256];
  snprintf(buffer, sizeof(buffer),
           "[Cycle %05d] PC: 0x%04llX | Inst: 0x%08X",
           cycle, pc, opcode);
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

void FlightRecorder::dump_vector_registers(const std::string &filepath)
{
  std::ofstream logfile(filepath);
  if (!logfile.is_open())
  {
    std::cerr << "[Recorder Error] Could not open log file: " << filepath << "\n";
    std::cerr << "                 (Does the 'outputs/' directory exist?)\n";
    return;
  }

  for (int i = 0; i < 256; i++)
  {
    logfile << "v" << std::dec << i << ": ";
    for (int lane = 0; lane < 32; lane++)
    {
      uint32_t val = zrVGPR(i, lane);
      logfile << std::hex << std::setw(8) << std::setfill('0') << val << " ";
    }
    logfile << "\n";
  }
  logfile.close();
}
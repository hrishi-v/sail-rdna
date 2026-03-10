#pragma once
#include <cstdint>
#include <gmp.h>

extern "C"
{
#include "sail.h"

  void model_init(void);

  unit zstep(unit);
  bool zget_halt_flag(unit);

  uint64_t zget_pc(unit);
  uint32_t zread_mem_32(uint64_t addr);

  unit zwrite_mem_8(uint64_t addr, uint64_t data);
  unit zwrite_mem_32(uint64_t addr, uint64_t data);
  unit zwSGPR(uint64_t reg, uint64_t data);
  unit zset_pc(uint64_t start_addr);

  unit zreset_vmcnt(unit);
  unit zreset_lgkmcnt(unit);
  unit zreset_halt_flag(unit);
};
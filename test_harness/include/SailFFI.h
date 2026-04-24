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
  unit zset_pc(uint64_t start_addr);

  uint32_t zget_sgpr(uint64_t reg);
  unit zwSGPR(uint64_t reg, uint32_t data);
  uint32_t zrVGPR(uint64_t reg, uint64_t lane_id);
  unit zwVGPR(uint64_t reg, uint64_t lane_id, uint32_t data);

  unit zreset_vmcnt(unit);
  unit zreset_vmq(unit);
  unit zreset_lgkmcnt(unit);
  unit zreset_pending_load_queue(unit);
  unit zreset_vscnt(unit);
  unit zreset_vsq_src_lock(unit);
  unit zreset_vlq(unit);
  unit zreset_halt_flag(unit);
  bool zget_error_flag(unit);
  unit zreset_error_flag(unit);
};

; store_vgpr_reuse.asm
; Overwrite source VGPR v2 while its global_store is still in flight
; (before s_waitcnt_vscnt null, 0x0).  Sail should emit:
;   [HAZARD] overwrite of v2 while store in flight (missing s_waitcnt_vscnt)
; On real HW this is the bug class from LLVM PR #77439: the memory write
; may sample the overwritten value instead of the intended one.

v_mov_b32 v10, s0             ; base addr lo
v_mov_b32 v11, s1             ; base addr hi

v_mov_b32 v2, 0xDEAD0001

global_store_b32 v[10:11], v2, off offset:0
v_mov_b32 v2, 0xBADC0FFE       ; HAZARD: v2 still locked by in-flight store
s_waitcnt_vscnt null, 0x0

global_load_b32 v0, v[10:11], off offset:0
s_waitcnt vmcnt(0)

s_endpgm

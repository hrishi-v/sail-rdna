; store_vgpr_reuse.asm — DISABLED
;
; Originally asserted that overwriting the source VGPR of an in-flight
; global_store before s_waitcnt_vscnt is a hazard, citing LLVM PR #77439.
;
; Empirically retracted: the four store_chain_* fuzzer kernels exhibit this
; exact pattern (LLVM-emitted) and produce correct memory contents on
; RX 7800XT (GFX1101) — see differential run, all dump=match. Store data is
; captured at issue, before the subsequent VALU writeback retires; VSCNT
; only gates load-after-store ordering, not source-register liveness.
; The VSQ source-lock model has been removed from the spec.
;
; This file is kept under tests/asm/disabled/ for thesis provenance.

v_mov_b32 v10, s0             ; base addr lo
v_mov_b32 v11, s1             ; base addr hi

v_mov_b32 v2, 0xDEAD0001

global_store_b32 v[10:11], v2, off offset:0
v_mov_b32 v2, 0xBADC0FFE       ; HAZARD: v2 still locked by in-flight store
s_waitcnt_vscnt null, 0x0

global_load_b32 v0, v[10:11], off offset:0
s_waitcnt vmcnt(0)

s_endpgm

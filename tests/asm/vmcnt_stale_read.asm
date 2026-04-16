; vmcnt_stale_read.asm
; Demonstrates stale VGPR read before s_waitcnt vmcnt(0).
; Setup: MEM32 0x2000 0xdeadbeef
; Expected: v3 = 0x11111111 (stale), v4 = 0xdeadbeef (after waitcnt)

s_mov_b32 exec_lo, -1

v_mov_b32 v0, 0x00002000
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0x11111111
global_load_b32 v2, v[0:1], off
v_mov_b32 v3, v2
s_waitcnt vmcnt(0)
v_mov_b32 v4, v2

s_endpgm

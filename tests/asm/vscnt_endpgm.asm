; vscnt_endpgm.asm
; Terminates with an outstanding vector store (VSCNT > 0).
; Sail should emit: [HAZARD] s_endpgm with outstanding vector stores
; Expected: v2 = 0xdeadbeef

s_mov_b32 exec_lo, -1

v_mov_b32 v0, 0x00002000
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0xDEADBEEF
global_store_b32 v[0:1], v2, off

s_endpgm

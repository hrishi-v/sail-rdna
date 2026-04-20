; vscnt_partial_wait.asm
; 3 stores → VSCNT=3, partial wait to 1, 1 more store → VSCNT=2, full drain.
; Expected (on real HW): v0..v3 = {0xDEAD0001, 0xDEAD0002, 0xDEAD0003, 0xDEAD0004}

v_mov_b32 v10, s0             ; base addr lo
v_mov_b32 v11, s1             ; base addr hi

v_mov_b32 v2, 0xDEAD0001
v_mov_b32 v3, 0xDEAD0002
v_mov_b32 v4, 0xDEAD0003
v_mov_b32 v5, 0xDEAD0004

global_store_b32 v[10:11], v2, off offset:0
global_store_b32 v[10:11], v3, off offset:4
global_store_b32 v[10:11], v4, off offset:8
; VSCNT should be 3 here
s_waitcnt_vscnt null, 0x1
; VSCNT should be 1 here (target: drain to 1)

global_store_b32 v[10:11], v5, off offset:12
; VSCNT should be 2 here
s_waitcnt_vscnt null, 0x0
; VSCNT should be 0 here

global_load_b32 v0, v[10:11], off offset:0
global_load_b32 v1, v[10:11], off offset:4
global_load_b32 v2, v[10:11], off offset:8
global_load_b32 v3, v[10:11], off offset:12
s_waitcnt vmcnt(0)

s_endpgm

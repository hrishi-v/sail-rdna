; v_cmpx_gt_u64_e64 v[0:1], v[2:3]
; Writes per-lane greater-than result into EXEC.
s_mov_b32 exec_lo, -1
v_mov_b32 v0, 0x000000FF       ; v[0:1] = 0xFF
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0x0000000A       ; v[2:3] = 10
v_mov_b32 v3, 0x00000000
v_cmpx_gt_u64_e64 v[0:1], v[2:3]   ; EXEC = all-ones (every lane: 0xFF > 0xA)
s_endpgm

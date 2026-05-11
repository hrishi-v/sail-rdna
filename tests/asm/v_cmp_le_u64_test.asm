; v_cmp_le_u64_e32 vcc_lo, v[0:1], v[2:3]
s_mov_b32 exec_lo, -1
v_mov_b32 v0, 0x00000005       ; v[0:1] = 5
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0x0000000A       ; v[2:3] = 10
v_mov_b32 v3, 0x00000000
v_cmp_le_u64_e32 vcc_lo, v[0:1], v[2:3]
s_endpgm

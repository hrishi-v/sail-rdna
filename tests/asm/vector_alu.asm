s_mov_b32 s0, 100
v_mov_b32 v0, 5

v_add_u32 v1, v0, s0   // v1 = v0 + s0

s_endpgm
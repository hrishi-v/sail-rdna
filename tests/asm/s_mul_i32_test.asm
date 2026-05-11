; s_mul_i32 s0, s1, s2: s0 = (s1 * s2)[31:0]
s_mov_b32 s1, 0x00000007
s_mov_b32 s2, 0x00000006
s_mul_i32 s0, s1, s2         ; s0 = 42
s_endpgm

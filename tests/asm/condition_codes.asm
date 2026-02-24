s_mov_b32 s0, 3
s_sub_u32 s0, s0, 1
s_cmp_eq_u32 s0, 0

s_cbranch_scc0 Label_Loop

s_endpgm
	s_mov_b32 exec_lo, -1  // AUTO-INJECTED: Turn on all 32 lanes
s_load_b32 s3, s[0:1], 0x1c
s_load_b64 s[4:5], s[0:1], 0x0
s_load_b32 s0, s[0:1], 0x8
s_waitcnt lgkmcnt(0)
s_and_b32 s3, s3, 0xffff
v_mad_u64_u32 v[1:2], null, s2, s3, v[0:1]
v_ashrrev_i32_e32 v2, 31, v1
v_lshlrev_b64 v[0:1], 2, v[1:2]
v_add_co_u32 v0, vcc_lo, s4, v0
v_add_co_ci_u32_e32 v1, vcc_lo, s5, v1, vcc_lo
global_load_b32 v2, v[0:1], off
s_waitcnt vmcnt(0)
v_add_nc_u32_e32 v2, s0, v2
global_store_b32 v[0:1], v2, off
s_endpgm

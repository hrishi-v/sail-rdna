"s_mov_b32 exec_lo, -1\n\t"
"v_mov_b32 v0, s24\n\t"
"v_mov_b32 v1, s25\n\t"
"v_mbcnt_lo_u32_b32 v4, -1, 0\n\t"
"v_lshlrev_b32 v4, 2, v4\n\t"
"v_add_co_u32 v0, vcc_lo, v0, v4\n\t"
"v_add_co_ci_u32_e64 v1, null, v1, 0, vcc_lo\n\t"

"v_mov_b32 v2, 0xCAFEBABE\n\t"
"flat_store_b32 v[0:1], v2\n\t"

"s_waitcnt_vscnt null, 0\n\t"

"flat_load_b32 v3, v[0:1]\n\t"
"s_waitcnt vmcnt(0)\n\t"
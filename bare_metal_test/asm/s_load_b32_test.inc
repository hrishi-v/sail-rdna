"v_mov_b32 v0, s24\n\t"
"v_mov_b32 v1, s25\n\t"
"v_mov_b32 v2, 0xDEADC0DE\n\t"

"flat_store_b32 v[0:1], v2 glc\n\t"
"s_waitcnt_vscnt null, 0\n\t"
"s_dcache_inv\n\t"

"s_load_b32 s2, s[24:25], 0\n\t"
"s_waitcnt lgkmcnt(0)\n\t"
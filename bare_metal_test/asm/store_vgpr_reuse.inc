"v_mov_b32 v10, s24\n\t"
"v_mov_b32 v11, s25\n\t"

"v_mov_b32 v2, 0xDEAD0001\n\t"

"global_store_b32 v[10:11], v2, off offset:0\n\t"
"v_mov_b32 v2, 0xBADC0FFE\n\t"
"s_waitcnt_vscnt null, 0x0\n\t"

"global_load_b32 v0, v[10:11], off offset:0\n\t"
"s_waitcnt vmcnt(0)\n\t"

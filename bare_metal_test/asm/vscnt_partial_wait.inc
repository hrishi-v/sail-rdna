"v_mov_b32 v10, s24\n\t"
"v_mov_b32 v11, s25\n\t"

"v_mov_b32 v2, 0xDEAD0001\n\t"
"v_mov_b32 v3, 0xDEAD0002\n\t"
"v_mov_b32 v4, 0xDEAD0003\n\t"
"v_mov_b32 v5, 0xDEAD0004\n\t"

"global_store_b32 v[10:11], v2, off offset:0\n\t"
"global_store_b32 v[10:11], v3, off offset:4\n\t"
"global_store_b32 v[10:11], v4, off offset:8\n\t"
"s_waitcnt_vscnt null, 0x1\n\t"

"global_store_b32 v[10:11], v5, off offset:12\n\t"
"s_waitcnt_vscnt null, 0x0\n\t"

"global_load_b32 v0, v[10:11], off offset:0\n\t"
"global_load_b32 v1, v[10:11], off offset:4\n\t"
"global_load_b32 v2, v[10:11], off offset:8\n\t"
"global_load_b32 v3, v[10:11], off offset:12\n\t"
"s_waitcnt vmcnt(0)\n\t"

"v_mov_b32 v14, %0\n\t"
"v_mov_b32 v15, %1\n\t"
"flat_store_b32 v[14:15], v2\n\t"
"s_waitcnt vmcnt(0)\n\t"

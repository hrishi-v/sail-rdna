"v_mov_b32 v2, %0\n\t"
"v_mov_b32 v3, %1\n\t"
"flat_store_b32 v[2:3], v5\n\t"
"s_waitcnt vmcnt(0)\n\t"

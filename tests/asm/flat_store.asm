s_mov_b32 exec_lo, -1
v_mov_b32 v0, 0x00002008
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0xCAFEBABE
flat_store_b32 v[0:1], v2
s_waitcnt vmcnt(0)
flat_load_b32 v3, v[0:1]
s_waitcnt vmcnt(0)
s_endpgm

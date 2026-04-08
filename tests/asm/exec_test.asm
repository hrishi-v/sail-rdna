v_mov_b32 v1, 0xAAAAAAAA
s_mov_b32 exec_lo, 0x2
s_waitcnt lgkmcnt(0)
v_mov_b32 v1, 0xBBBBBBBB   // Update v1[1]

s_mov_b32 exec_lo, 0xFFFFFFFF // Restore
s_waitcnt lgkmcnt(0)         // FORCE SYNC
v_mov_b32 v0, v1             // Copy v1 to v0
s_endpgm
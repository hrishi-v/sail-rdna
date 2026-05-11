; s_or_b32 s0, s1, s2: s0 = s1 | s2, SCC = (result != 0)
s_mov_b32 s1, 0xF0F00000
s_mov_b32 s2, 0x0000F0F0
s_or_b32 s0, s1, s2          ; s0 = 0xF0F0F0F0, SCC = 1
s_endpgm

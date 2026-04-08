; s_and_not1_b32_test.asm
; s1 = 0xFF00FF00, s2 = 0x0F0F0F0F
; s0 = s1 & ~s2 = 0xFF00FF00 & 0xF0F0F0F0 = 0xF000F000, SCC = 1

s_mov_b32 s1, 0xFF00FF00
s_mov_b32 s2, 0x0F0F0F0F
s_and_not1_b32 s0, s1, s2
s_endpgm

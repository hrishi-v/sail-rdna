; s_and_b32_test.asm
; s_and_b32 s0, s1, s2
; s1 = 0xFFFF0000, s2 = 0x0FFFFFFF
; 0xFFFF0000 & 0x0FFFFFFF = 0x0FFF0000
; Expected: s0 = 0x0FFF0000, SCC = 1 (result non-zero)

s_mov_b32 s1, 0xFFFF0000
s_mov_b32 s2, 0x0FFFFFFF
s_and_b32 s0, s1, s2

s_endpgm

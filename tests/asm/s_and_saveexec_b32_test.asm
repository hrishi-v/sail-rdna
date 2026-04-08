; s_and_saveexec_b32_test.asm
; EXEC_LO starts as 0xFFFFFFFF (all 32 lanes active)
; s1 = 0x0000FFFF (lower 16 lanes mask)
; After: s0 = old EXEC_LO = 0xFFFFFFFF, EXEC_LO = 0xFFFFFFFF & 0x0000FFFF = 0x0000FFFF

s_mov_b32 s1, 0x0000FFFF
s_and_saveexec_b32 s0, s1
s_endpgm

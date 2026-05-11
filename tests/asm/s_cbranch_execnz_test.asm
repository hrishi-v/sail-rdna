; s_cbranch_execnz: branch taken when EXEC != 0
s_mov_b32 exec_lo, -1
s_cbranch_execnz taken
s_mov_b32 s0, 0xDEAD           ; should be skipped
taken:
s_mov_b32 s1, 0xBEEF
s_endpgm

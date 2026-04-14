s_mov_b32 s0, 0x00002000
s_mov_b32 s1, 0x00000000

; Poison value
s_mov_b32 s2, 0x11111111

; Load value from memory
s_load_b32 s2, s[0:1], 0x0

; NO waitcnt — read s2 immediately
v_mov_b32 v0, s2

; Now wait and read again as the manual dictates
s_waitcnt lgkmcnt(0)
v_mov_b32 v1, s2

s_endpgm
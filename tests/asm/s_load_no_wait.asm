s_mov_b32 s0, 0x00002000
s_mov_b32 s1, 0x00000000

; Pre-poison s2 so we can distinguish "stale" from "uninitialised"
s_mov_b32 s2, 0x11111111

; Fire off a scalar load
s_load_b32 s2, s[0:1], 0x0

; NO waitcnt — read s2 immediately
v_mov_b32 v0, s2

; Now wait and read again for comparison
s_waitcnt lgkmcnt(0)
v_mov_b32 v1, s2

s_endpgm
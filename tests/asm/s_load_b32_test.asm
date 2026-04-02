; s_load_b32_test.asm
; Store a value to memory via flat_store, then load it back via s_load_b32
; Expected: s2 = 0xDEADC0DE

s_mov_b32 s0, 0x00002000    ; base_lo
s_mov_b32 s1, 0x00000000    ; base_hi

; Write known value to memory via flat_store (scalar load needs something there)
s_mov_b32 exec_lo, -1
v_mov_b32 v0, 0x00002000
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0xDEADC0DE
flat_store_b32 v[0:1], v2

s_load_b32 s2, s[0:1], 0x0
s_waitcnt lgkmcnt(0)

s_endpgm

; v_ashrrev_i32_test.asm
; v_ashrrev_i32_e32 v0, 3, v1
; v1 = 0x80000008 (negative, MSB set), shift_amount = 3 (inline constant)
; Arithmetic right shift fills with sign bit (1), so:
; 0x80000008 >> 3 = 0xF0000001
; Expected: v0 = 0xF0000001

s_mov_b32 exec_lo, -1

v_mov_b32 v0, 0x80000008
v_ashrrev_i32_e32 v0, 3, v0

s_endpgm

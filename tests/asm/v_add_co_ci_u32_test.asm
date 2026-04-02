; v_add_co_ci_u32_test.asm
; v_add_co_ci_u32_e32 v0, s10, v2
; VCC_LO = 0xFFFFFFFF (carry-in = 1 for all lanes)
; s10 = 0xFFFFFFFF, v2 = 0x00000000
; 0xFFFFFFFF + 0x00000000 + 1(carry) = 0x100000000 (overflows u32)
; Expected: v0 = 0x00000000, VCC_LO = 0xFFFFFFFF (carry-out in all lanes)
; v1 = VCC_LO = 0xFFFFFFFF

s_mov_b32 exec_lo, -1

s_mov_b32 vcc_lo, 0xFFFFFFFF   ; carry-in = 1 for all 32 lanes
s_mov_b32 s10, 0xFFFFFFFF
v_mov_b32 v2, 0x00000000

v_add_co_ci_u32_e32 v0, s10, v2

v_mov_b32 v1, vcc_lo            ; capture carry-out

s_endpgm

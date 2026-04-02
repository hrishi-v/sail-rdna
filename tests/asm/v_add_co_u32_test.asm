; v_add_co_u32_test.asm
; v_add_co_u32 v0, vcc_lo, s10, v0
; s10 = 0xFFFFFFFF, v0 = 0x00000002
; 0xFFFFFFFF + 0x00000002 = 0x100000001 (overflows u32)
; Expected: v0 = 0x00000001, vcc_lo = 0xFFFFFFFF (carry in all 32 lanes)

s_mov_b32 exec_lo, -1

s_mov_b32 s10, 0xFFFFFFFF
v_mov_b32 v0, 0x00000002

v_add_co_u32 v0, vcc_lo, s10, v0

v_mov_b32 v1, vcc_lo          ; capture carry output

s_endpgm

; v_lshlrev_b64_test.asm
; v_lshlrev_b64 v[0:1], 1, v[2:3]
; value = {lo: 0x80000001, hi: 0x00000000}
; 0x0000000080000001 << 1 = 0x0000000100000002
; Expected: v0 = 0x00000002 (lo), v1 = 0x00000001 (hi)

s_mov_b32 exec_lo, -1

v_mov_b32 v2, 0x80000001   ; value lo (bit 31 set — tests cross-word carry)
v_mov_b32 v3, 0x00000000   ; value hi

v_lshlrev_b64 v[0:1], 1, v[2:3]

s_endpgm

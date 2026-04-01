; v_mad_u64_test.asm
; v_mad_u64_u32 v[0:1], null, s0, s1, v[2:3]
; s0 = s1 = 65536 (0x10000), addend v[2:3] = {1, 0}
; 65536 * 65536 + 1 = 0x1_00000001
; Expected: v0 = 0x00000001 (low), v1 = 0x00000001 (high)

s_mov_b32 exec_lo, -1

s_mov_b32 s0, 0x00010000   ; src0 = 65536
s_mov_b32 s1, 0x00010000   ; src1 = 65536

v_mov_b32 v2, 0x00000001   ; addend lo = 1
v_mov_b32 v3, 0x00000000   ; addend hi = 0

v_mad_u64_u32 v[0:1], null, s0, s1, v[2:3]

s_endpgm

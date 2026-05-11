; s_addc_u32 sdst, ssrc0, ssrc1: result = ssrc0 + ssrc1 + SCC
; Seed SCC by overflowing an add, then add with carry.
s_mov_b32 s1, 0xFFFFFFFF
s_mov_b32 s2, 0x00000001
s_add_u32 s0, s1, s2         ; s0 = 0, SCC = 1
s_mov_b32 s3, 0x00000010
s_mov_b32 s4, 0x00000020
s_addc_u32 s5, s3, s4        ; s5 = 0x31 (0x10 + 0x20 + 1)
s_endpgm

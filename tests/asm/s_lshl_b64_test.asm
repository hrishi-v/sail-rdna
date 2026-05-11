; s_lshl_b64 s[0:1], s[2:3], s4: 64-bit logical left shift
s_mov_b32 s2, 0x00000001
s_mov_b32 s3, 0x00000000
s_mov_b32 s4, 0x00000020       ; shift by 32
s_lshl_b64 s[0:1], s[2:3], s4  ; s[0:1] = 0x0000000100000000, SCC = 1
s_endpgm

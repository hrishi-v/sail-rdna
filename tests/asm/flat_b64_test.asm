; flat_b64_test.asm
; Store a 64-bit value to memory via flat_store_b64, then load it back
; via flat_load_b64 and verify both halves land in v[0:1]

s_mov_b32 exec_lo, -1

; Address in v[2:3] pointing to known memory at 0x00002000
v_mov_b32 v2, 0x00002000
v_mov_b32 v3, 0x00000000

; Known 64-bit value split across v[4:5]
v_mov_b32 v4, 0xDEADBEEF   ; low 32 bits
v_mov_b32 v5, 0xCAFEBABE   ; high 32 bits

; Store 64 bits to memory
flat_store_b64 v[2:3], v[4:5]

; Load 64 bits back into v[0:1]
flat_load_b64 v[0:1], v[2:3]
s_waitcnt vmcnt(0)

s_endpgm

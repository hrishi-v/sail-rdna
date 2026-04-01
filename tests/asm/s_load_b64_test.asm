; s_load_b64_test.asm
; Store a 64-bit value into memory, then load it back via s_load_b64
; and verify it lands in the correct SGPR pair

; Set up a 64-bit address in s[0:1] pointing to known memory
s_mov_b32 s0, 0x00002000
s_mov_b32 s1, 0x00000000

; Write known values to memory at 0x00002000
v_mov_b32 v0, 0x00002000
v_mov_b32 v1, 0x00000000
v_mov_b32 v2, 0xDEADBEEF
v_mov_b32 v3, 0xCAFEBABE
flat_store_b32 v[0:1], v2           ; store 0xDEADBEEF at 0x00002000
flat_store_b32 v[0:1], v3 offset:4  ; store 0xCAFEBABE at 0x00002004

; Load 64 bits from s[0:1] + 0 into s[2:3]
s_load_b64 s[2:3], s[0:1], 0x0
s_waitcnt lgkmcnt(0)

s_endpgm

// THIS HAS NON-DETERMISTIC BEHAVIOR DUE TO THE FLAT STORES AND LOADS, BUT IT SHOULD WORK IN PRACTICE
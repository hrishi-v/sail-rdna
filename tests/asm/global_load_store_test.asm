; global_load_store_test.asm
; Verify global_store_b32 writes to memory and global_load_b32 reads it back
; Uses saddr=off (null) so address comes from VGPR pair, same as flat
; Expected: v0 = 0xDEADC0DE

s_mov_b32 exec_lo, -1

v_mov_b32 v2, 0x00002000    ; addr_lo
v_mov_b32 v3, 0x00000000    ; addr_hi

v_mov_b32 v1, 0xDEADC0DE
global_store_b32 v[2:3], v1, off
s_waitcnt vmcnt(0)

global_load_b32 v0, v[2:3], off
s_waitcnt vmcnt(0)

s_endpgm

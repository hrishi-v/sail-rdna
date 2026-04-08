; read_modify_write.asm
; Mirrors the bare-metal HIP kernel:
;   int result = mem_buf[0] + tid + 100;
;
; Setup (from tests/setups/read_modify_write.setup):
;   s[2:3] = 0x1000  (mem_buf pointer, set by conftest-generated setup file)
;   v0     = lane id (hardware-initialised: 0..31)
;
; After execution v4 holds result for each lane.

v_mov_b32 v1, 0                       ; address offset = 0 (mem_buf[0])
global_load_b32 v4, v1, s[2:3]        ; v4 = mem_buf[0]
s_waitcnt vmcnt(0)
v_add3_u32 v4, 0x64, v4, v0           ; v4 = 100 + mem_val + tid
s_endpgm

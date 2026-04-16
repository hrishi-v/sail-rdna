; divergence_zero_exec_test.asm
; Tests two edge cases:
;   (a) EXEC becomes all-zero via s_and_saveexec_b32 (SCC=0 should fire)
;   (b) Reconvergence: after restoring EXEC, a subsequent vector op sees all lanes.
;
; Setup: EXEC_LO = 0xFFFFFFFF, v0 = 0xDEADBEEF (all lanes)
;
; Expected:
;   s0 = 0xFFFFFFFF (saved exec)
;   EXEC after AND = 0x00000000 (nothing active)
;   v0 unchanged = 0xDEADBEEF for all lanes (vector write with EXEC=0 is a no-op)
;   After reconverge: v0 = 0x00000001 for all lanes (v_mov writes with full EXEC)

v_mov_b32 v0, 0xDEADBEEF          ; prime all lanes

; Zero out EXEC via saveexec with mask 0
s_mov_b32 s1, 0x00000000
s_and_saveexec_b32 s0, s1          ; s0 = 0xFFFFFFFF, EXEC = 0x00000000, SCC = 0

; This v_mov should be a complete no-op (EXEC=0, no lane active)
v_mov_b32 v0, 0xCAFEBABE

; Restore EXEC and write a known value to confirm reconvergence
s_mov_b32 exec_lo, s0              ; EXEC = 0xFFFFFFFF
v_mov_b32 v0, 0x00000001           ; all lanes should now get 0x00000001

s_endpgm

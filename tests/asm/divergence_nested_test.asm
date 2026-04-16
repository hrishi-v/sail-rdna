; divergence_nested_test.asm
; Tests nested divergence: outer branch splits lanes 0-15 vs 16-31,
; inner branch (within the "low" half) further splits lanes 0-7 vs 8-15.
;
; Setup: v0[lane] = lane index (pre-loaded by harness: v0 = 0,1,2,...,31)
;        v1 = result register, v2 = saved outer exec, v3 = saved inner exec
;
; Expected final v1 per lane:
;   lanes  0- 7: 0xAAAA0000  (outer-low AND inner-low path)
;   lanes  8-15: 0xBBBB0000  (outer-low AND inner-high path)
;   lanes 16-31: 0xCCCC0000  (outer-high path)
;
; Outer branch: EXEC = lanes 0-15 vs 16-31  (mask 0x0000FFFF vs 0xFFFF0000)
; Inner branch: EXEC = lanes 0-7 vs 8-15   (mask 0x000000FF vs 0x0000FF00)

; --- Outer "if" (lanes 0-15): s1 = 0x0000FFFF ---
s_mov_b32 s1, 0x0000FFFF
s_and_saveexec_b32 s2, s1          ; s2 = old EXEC (0xFFFFFFFF), EXEC = 0x0000FFFF

  ; --- Inner "if" (lanes 0-7): s3 = 0x000000FF ---
  s_mov_b32 s3, 0x000000FF
  s_and_saveexec_b32 s4, s3        ; s4 = 0x0000FFFF, EXEC = 0x000000FF
  v_mov_b32 v1, 0xAAAA0000         ; only lanes 0-7 written

  ; --- Inner "else" (lanes 8-15): restore then complement ---
  s_and_not1_b32 exec_lo, s4, exec_lo  ; EXEC = 0x0000FFFF & ~0x000000FF = 0x0000FF00
  v_mov_b32 v1, 0xBBBB0000             ; only lanes 8-15 written

  ; --- Restore inner exec ---
  s_mov_b32 exec_lo, s4            ; EXEC = 0x0000FFFF

; --- Outer "else" (lanes 16-31): restore then complement ---
s_and_not1_b32 exec_lo, s2, exec_lo  ; EXEC = 0xFFFFFFFF & ~0x0000FFFF = 0xFFFF0000
v_mov_b32 v1, 0xCCCC0000              ; only lanes 16-31 written

; --- Reconverge: restore full exec ---
s_mov_b32 exec_lo, s2              ; EXEC = 0xFFFFFFFF

; Post-divergence vector op: all lanes add 1 to v1
v_add_nc_u32 v1, v1, 1

s_endpgm

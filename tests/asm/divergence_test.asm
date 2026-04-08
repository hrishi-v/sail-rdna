; divergence_test.asm
; v0 = lane IDs (0..31), initialized by setup via vgpr_lane_ids: [0]
; Expected: v4[lane] = 0xAAAAAAAA if lane < 16, else 0xBBBBBBBB
;
; v_cmp_gt_i32 sets vcc[lane] = (16 > lane), i.e. 1 for lanes 0-15
; v_cndmask_b32 selects src1 (v1 = 0xAAAAAAAA) when vcc=1, src0 (0xBBBBBBBB) when vcc=0

v_mov_b32_e32 v1, 0xaaaaaaaa
v_cmp_gt_i32_e32 vcc_lo, 16, v0
v_cndmask_b32_e32 v4, 0xbbbbbbbb, v1, vcc_lo
s_endpgm

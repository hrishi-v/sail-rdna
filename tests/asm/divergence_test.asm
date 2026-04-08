	s_clause 0x1
	s_load_b32 s2, s[0:1], 0x24
	s_load_b64 s[0:1], s[0:1], 0x0
	s_waitcnt lgkmcnt(0)
	s_and_b32 s2, s2, 0xffff
	s_delay_alu instid0(SALU_CYCLE_1) | instskip(SKIP_1) | instid1(VALU_DEP_2)
	v_mad_u64_u32 v[1:2], null, s15, s2, v[0:1]
	v_mov_b32_e32 v0, 0xaaaaaaaa
	v_ashrrev_i32_e32 v2, 31, v1
	v_cmp_gt_i32_e32 vcc_lo, 16, v1
	s_delay_alu instid0(VALU_DEP_2) | instskip(NEXT) | instid1(VALU_DEP_4)
	v_lshlrev_b64 v[2:3], 2, v[1:2]
	v_cndmask_b32_e32 v4, 0xbbbbbbbb, v0, vcc_lo
	s_delay_alu instid0(VALU_DEP_2) | instskip(NEXT) | instid1(VALU_DEP_3)
	v_add_co_u32 v0, vcc_lo, s0, v2
	v_add_co_ci_u32_e32 v1, vcc_lo, s1, v3, vcc_lo
	global_store_b32 v[0:1], v4, off
	s_endpgm
f:
	s_clause 0x1
	s_load_b64 s[0:1], s[4:5], 0x24
	s_load_b32 s2, s[4:5], 0x2c
	v_and_b32_e32 v0, 0x3ff, v0
	s_delay_alu instid0(VALU_DEP_1) | instskip(SKIP_1) | instid1(VALU_DEP_1)
	v_lshlrev_b32_e32 v0, 2, v0
	s_waitcnt lgkmcnt(0)
	v_add_co_u32 v0, s0, s0, v0
	s_delay_alu instid0(VALU_DEP_1)
	v_add_co_ci_u32_e64 v1, null, s1, 0, s0
	s_bitcmp0_b32 s2, 0
	scratch_store_b64 off, v[0:1], off      ; 8-byte Folded Spill
	flat_load_b32 v0, v[0:1]
	s_waitcnt vmcnt(0) lgkmcnt(0)
	scratch_store_b32 off, v0, off offset:8 ; 4-byte Folded Spill
	s_cbranch_scc1 .LBB0_2
  
; %bb.1:                                ; %true
	s_clause 0x1                            ; 12-byte Folded Reload
	scratch_load_b64 v[0:1], off, off
	scratch_load_b32 v2, off, off offset:8
	s_waitcnt vmcnt(0)
	flat_store_b32 v[0:1], v2
.LBB0_2:                                ; %false
	s_nop 0
	s_sendmsg sendmsg(MSG_DEALLOC_VGPRS)
	s_endpgm
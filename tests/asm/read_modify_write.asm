	s_load_b64 s[0:1], s[0:1], 0x0
	v_lshl_add_u32 v1, v0, 1, 0x64
	v_lshlrev_b32_e32 v0, 2, v0
	s_waitcnt lgkmcnt(0)
	global_store_b32 v0, v1, s[0:1]
	s_endpgm

	.section	.AMDGPU.config,"",@progbits
	.long	47176
	.long	3769565215
	.long	47180
	.long	5019
	.long	47200
	.long	8192
	.long	4
	.long	0
	.long	8
	.long	3
	.text
	.globl	f                               ; -- Begin function f
	.p2align	8
	.type	f,@function
f:                                      ; @f
; %bb.0:
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
	;;#ASMSTART
	; clobber
	;;#ASMEND
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
.Lfunc_end0:
	.size	f, .Lfunc_end0-f
                                        ; -- End function
	.set f.num_vgpr, 256
	.set f.num_agpr, 0
	.set f.numbered_sgpr, 6
	.set f.num_named_barrier, 0
	.set f.private_seg_size, 16
	.set f.uses_vcc, 0
	.set f.uses_flat_scratch, 1
	.set f.has_dyn_sized_stack, 0
	.set f.has_recursion, 0
	.set f.has_indirect_call, 0
	.section	.AMDGPU.csdata,"",@progbits
; Kernel info:
; codeLenInByte = 140
; TotalNumSgprs: 6
; NumVgprs: 256
; ScratchSize: 16
; MemoryBound: 0
; FloatMode: 240
; IeeeMode: 1
; LDSByteSize: 0 bytes/workgroup (compile time only)
; SGPRBlocks: 0
; VGPRBlocks: 31
; NumSGPRsForWavesPerEU: 6
; NumVGPRsForWavesPerEU: 256
; Occupancy: 5
; WaveLimiterHint : 0
; COMPUTE_PGM_RSRC2:SCRATCH_EN: 1
; COMPUTE_PGM_RSRC2:USER_SGPR: 13
; COMPUTE_PGM_RSRC2:TRAP_HANDLER: 0
; COMPUTE_PGM_RSRC2:TGID_X_EN: 1
; COMPUTE_PGM_RSRC2:TGID_Y_EN: 1
; COMPUTE_PGM_RSRC2:TGID_Z_EN: 1
; COMPUTE_PGM_RSRC2:TIDIG_COMP_CNT: 2
	.section	.AMDGPU.gpr_maximums,"",@progbits
	.set amdgpu.max_num_vgpr, 0
	.set amdgpu.max_num_agpr, 0
	.set amdgpu.max_num_sgpr, 0
	.set amdgpu.max_num_named_barrier, 0
	.section	.AMDGPU.csdata,"",@progbits
	.section	".note.GNU-stack","",@progbits
	.amd_amdgpu_isa "amdgcn----gfx1100"

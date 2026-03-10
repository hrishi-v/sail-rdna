	.amdgcn_target "amdgcn-amd-amdhsa--gfx1100"
	.amdhsa_code_object_version 5
	.text
	.weak	__cxa_pure_virtual              ; -- Begin function __cxa_pure_virtual
	.p2align	2
	.type	__cxa_pure_virtual,@function
__cxa_pure_virtual:                     ; @__cxa_pure_virtual
; %bb.0:
	s_waitcnt vmcnt(0) expcnt(0) lgkmcnt(0)
	s_mov_b32 s1, s33
	s_mov_b32 s33, s32
	s_trap 2
	s_sendmsg_rtn_b32 s0, sendmsg(MSG_RTN_GET_DOORBELL)
	s_mov_b32 ttmp2, m0
	s_waitcnt lgkmcnt(0)
	s_and_b32 s0, s0, 0x3ff
	s_or_b32 s0, s0, 0x400
	s_mov_b32 m0, s0
	s_sendmsg sendmsg(MSG_INTERRUPT)
	s_mov_b32 m0, ttmp2
.LBB0_1:                                ; =>This Inner Loop Header: Depth=1
	s_sethalt 5
	s_branch .LBB0_1
.Lfunc_end0:
	.size	__cxa_pure_virtual, .Lfunc_end0-__cxa_pure_virtual
                                        ; -- End function
	.set __cxa_pure_virtual.num_vgpr, 0
	.set __cxa_pure_virtual.num_agpr, 0
	.set __cxa_pure_virtual.numbered_sgpr, 34
	.set __cxa_pure_virtual.private_seg_size, 0
	.set __cxa_pure_virtual.uses_vcc, 0
	.set __cxa_pure_virtual.uses_flat_scratch, 0
	.set __cxa_pure_virtual.has_dyn_sized_stack, 0
	.set __cxa_pure_virtual.has_recursion, 0
	.set __cxa_pure_virtual.has_indirect_call, 0
	.section	.AMDGPU.csdata,"",@progbits
; Function info:
; codeLenInByte = 64
; TotalNumSgprs: 34
; NumVgprs: 0
; ScratchSize: 0
; MemoryBound: 0
	.text
	.weak	__cxa_deleted_virtual           ; -- Begin function __cxa_deleted_virtual
	.p2align	2
	.type	__cxa_deleted_virtual,@function
__cxa_deleted_virtual:                  ; @__cxa_deleted_virtual
; %bb.0:
	s_waitcnt vmcnt(0) expcnt(0) lgkmcnt(0)
	s_mov_b32 s1, s33
	s_mov_b32 s33, s32
	s_trap 2
	s_sendmsg_rtn_b32 s0, sendmsg(MSG_RTN_GET_DOORBELL)
	s_mov_b32 ttmp2, m0
	s_waitcnt lgkmcnt(0)
	s_and_b32 s0, s0, 0x3ff
	s_or_b32 s0, s0, 0x400
	s_mov_b32 m0, s0
	s_sendmsg sendmsg(MSG_INTERRUPT)
	s_mov_b32 m0, ttmp2
.LBB1_1:                                ; =>This Inner Loop Header: Depth=1
	s_sethalt 5
	s_branch .LBB1_1
.Lfunc_end1:
	.size	__cxa_deleted_virtual, .Lfunc_end1-__cxa_deleted_virtual
                                        ; -- End function
	.set __cxa_deleted_virtual.num_vgpr, 0
	.set __cxa_deleted_virtual.num_agpr, 0
	.set __cxa_deleted_virtual.numbered_sgpr, 34
	.set __cxa_deleted_virtual.private_seg_size, 0
	.set __cxa_deleted_virtual.uses_vcc, 0
	.set __cxa_deleted_virtual.uses_flat_scratch, 0
	.set __cxa_deleted_virtual.has_dyn_sized_stack, 0
	.set __cxa_deleted_virtual.has_recursion, 0
	.set __cxa_deleted_virtual.has_indirect_call, 0
	.section	.AMDGPU.csdata,"",@progbits
; Function info:
; codeLenInByte = 64
; TotalNumSgprs: 34
; NumVgprs: 0
; ScratchSize: 0
; MemoryBound: 0
	.text
	.protected	E                       ; -- Begin function E
	.globl	E
	.p2align	8
	.type	E,@function
E:                                      ; @E
; %bb.0:
	s_mov_b32 s33, 0
	s_load_b64 s[20:21], s[4:5], 0x0
	s_load_b64 s[16:17], s[4:5], 0x8
	s_load_b64 s[12:13], s[4:5], 0x10
	s_mov_b64 s[2:3], 0
	s_mov_b32 s23, s3
	s_mov_b64 s[0:1], src_private_base
	s_mov_b32 s4, 32
	s_lshr_b64 s[4:5], s[0:1], s4
	s_mov_b32 s24, -1
	s_mov_b32 s1, s33
	s_cmp_lg_u32 s1, s24
	s_mov_b32 s22, s4
	s_cselect_b32 s0, s22, s23
	s_mov_b32 s3, s2
	s_cselect_b32 s18, s1, s3
                                        ; kill: def $sgpr18 killed $sgpr18 def $sgpr18_sgpr19
	s_mov_b32 s19, s0
	s_add_i32 s0, s33, 8
	s_mov_b32 s1, s0
	s_cmp_lg_u32 s1, s24
	s_cselect_b32 s0, s22, s23
	s_cselect_b32 s14, s1, s3
                                        ; kill: def $sgpr14 killed $sgpr14 def $sgpr14_sgpr15
	s_mov_b32 s15, s0
	s_add_i32 s0, s33, 16
	s_mov_b32 s1, s0
	s_cmp_lg_u32 s1, s24
	s_cselect_b32 s0, s22, s23
	s_cselect_b32 s10, s1, s3
                                        ; kill: def $sgpr10 killed $sgpr10 def $sgpr10_sgpr11
	s_mov_b32 s11, s0
	s_add_i32 s1, s33, 24
	s_mov_b32 s0, s1
	s_cmp_lg_u32 s0, s24
	s_cselect_b32 s2, s22, s23
	s_cselect_b32 s0, s0, s3
                                        ; kill: def $sgpr0 killed $sgpr0 def $sgpr0_sgpr1
	s_mov_b32 s1, s2
	s_add_i32 s2, s33, 32
	s_mov_b32 s4, s2
	s_cmp_lg_u32 s4, s24
	s_cselect_b32 s2, s22, s23
	s_cselect_b32 s8, s4, s3
                                        ; kill: def $sgpr8 killed $sgpr8 def $sgpr8_sgpr9
	s_mov_b32 s9, s2
	s_add_i32 s2, s33, 40
	s_mov_b32 s4, s2
	s_cmp_lg_u32 s4, s24
	s_cselect_b32 s2, s22, s23
	s_cselect_b32 s6, s4, s3
                                        ; kill: def $sgpr6 killed $sgpr6 def $sgpr6_sgpr7
	s_mov_b32 s7, s2
	s_add_i32 s2, s33, 48
	s_mov_b32 s4, s2
	s_cmp_lg_u32 s4, s24
	s_cselect_b32 s2, s22, s23
	s_cselect_b32 s4, s4, s3
                                        ; kill: def $sgpr4 killed $sgpr4 def $sgpr4_sgpr5
	s_mov_b32 s5, s2
	s_add_i32 s25, s33, 52
	s_mov_b32 s2, s25
	s_cmp_lg_u32 s2, s24
	s_cselect_b32 s22, s22, s23
	s_cselect_b32 s2, s2, s3
                                        ; kill: def $sgpr2 killed $sgpr2 def $sgpr2_sgpr3
	s_mov_b32 s3, s22
	v_mov_b32_e32 v0, s18
	v_mov_b32_e32 v1, s19
	s_waitcnt lgkmcnt(0)
	v_mov_b32_e32 v2, s20
	v_mov_b32_e32 v3, s21
	flat_store_b64 v[0:1], v[2:3]
	v_mov_b32_e32 v0, s18
	v_mov_b32_e32 v1, s19
	flat_load_b64 v[6:7], v[0:1]
	v_mov_b32_e32 v0, s14
	v_mov_b32_e32 v1, s15
	v_mov_b32_e32 v2, s16
	v_mov_b32_e32 v3, s17
	flat_store_b64 v[0:1], v[2:3]
	v_mov_b32_e32 v0, s14
	v_mov_b32_e32 v1, s15
	flat_load_b64 v[4:5], v[0:1]
	v_mov_b32_e32 v0, s10
	v_mov_b32_e32 v1, s11
	v_mov_b32_e32 v2, s12
	v_mov_b32_e32 v3, s13
	flat_store_b64 v[0:1], v[2:3]
	v_mov_b32_e32 v0, s10
	v_mov_b32_e32 v1, s11
	flat_load_b64 v[2:3], v[0:1]
	v_mov_b32_e32 v0, s0
	v_mov_b32_e32 v1, s1
	s_waitcnt vmcnt(2) lgkmcnt(4)
	flat_store_b64 v[0:1], v[6:7]
	v_mov_b32_e32 v0, s8
	v_mov_b32_e32 v1, s9
	s_waitcnt vmcnt(1) lgkmcnt(3)
	flat_store_b64 v[0:1], v[4:5]
	v_mov_b32_e32 v0, s6
	v_mov_b32_e32 v1, s7
	s_waitcnt vmcnt(0) lgkmcnt(2)
	flat_store_b64 v[0:1], v[2:3]
	v_mov_b32_e32 v0, s8
	v_mov_b32_e32 v1, s9
	flat_load_b64 v[0:1], v[0:1]
	s_waitcnt vmcnt(0) lgkmcnt(0)
	flat_load_b32 v2, v[0:1]
	v_mov_b32_e32 v0, s4
	v_mov_b32_e32 v1, s5
	s_waitcnt vmcnt(0) lgkmcnt(0)
	flat_store_b32 v[0:1], v2
	v_mov_b32_e32 v0, s6
	v_mov_b32_e32 v1, s7
	flat_load_b64 v[0:1], v[0:1]
	s_waitcnt vmcnt(0) lgkmcnt(0)
	flat_load_b32 v2, v[0:1]
	v_mov_b32_e32 v0, s2
	v_mov_b32_e32 v1, s3
	s_waitcnt vmcnt(0) lgkmcnt(0)
	flat_store_b32 v[0:1], v2
	v_mov_b32_e32 v0, s4
	v_mov_b32_e32 v1, s5
	flat_load_b32 v0, v[0:1]
	v_mov_b32_e32 v1, s2
	v_mov_b32_e32 v2, s3
	flat_load_b32 v1, v[1:2]
	s_waitcnt vmcnt(0) lgkmcnt(0)
	v_add_nc_u32_e64 v2, v0, v1
	v_mov_b32_e32 v0, s0
	v_mov_b32_e32 v1, s1
	flat_load_b64 v[0:1], v[0:1]
	s_waitcnt vmcnt(0) lgkmcnt(0)
	flat_store_b32 v[0:1], v2
	s_endpgm
	.section	.rodata,"a",@progbits
	.p2align	6, 0x0
	.amdhsa_kernel E
		.amdhsa_group_segment_fixed_size 0
		.amdhsa_private_segment_fixed_size 64
		.amdhsa_kernarg_size 280
		.amdhsa_user_sgpr_count 13
		.amdhsa_user_sgpr_dispatch_ptr 1
		.amdhsa_user_sgpr_queue_ptr 1
		.amdhsa_user_sgpr_kernarg_segment_ptr 1
		.amdhsa_user_sgpr_dispatch_id 1
		.amdhsa_user_sgpr_private_segment_size 0
		.amdhsa_wavefront_size32 1
		.amdhsa_uses_dynamic_stack 0
		.amdhsa_enable_private_segment 1
		.amdhsa_system_sgpr_workgroup_id_x 1
		.amdhsa_system_sgpr_workgroup_id_y 1
		.amdhsa_system_sgpr_workgroup_id_z 1
		.amdhsa_system_sgpr_workgroup_info 0
		.amdhsa_system_vgpr_workitem_id 0
		.amdhsa_next_free_vgpr 8
		.amdhsa_next_free_sgpr 34
		.amdhsa_reserve_vcc 0
		.amdhsa_float_round_mode_32 0
		.amdhsa_float_round_mode_16_64 0
		.amdhsa_float_denorm_mode_32 3
		.amdhsa_float_denorm_mode_16_64 3
		.amdhsa_dx10_clamp 1
		.amdhsa_ieee_mode 1
		.amdhsa_fp16_overflow 0
		.amdhsa_workgroup_processor_mode 1
		.amdhsa_memory_ordered 1
		.amdhsa_forward_progress 1
		.amdhsa_shared_vgpr_count 0
		.amdhsa_exception_fp_ieee_invalid_op 0
		.amdhsa_exception_fp_denorm_src 0
		.amdhsa_exception_fp_ieee_div_zero 0
		.amdhsa_exception_fp_ieee_overflow 0
		.amdhsa_exception_fp_ieee_underflow 0
		.amdhsa_exception_fp_ieee_inexact 0
		.amdhsa_exception_int_div_zero 0
	.end_amdhsa_kernel
	.text
.Lfunc_end2:
	.size	E, .Lfunc_end2-E
                                        ; -- End function
	.set E.num_vgpr, 8
	.set E.num_agpr, 0
	.set E.numbered_sgpr, 34
	.set E.private_seg_size, 64
	.set E.uses_vcc, 0
	.set E.uses_flat_scratch, 0
	.set E.has_dyn_sized_stack, 0
	.set E.has_recursion, 0
	.set E.has_indirect_call, 0
	.section	.AMDGPU.csdata,"",@progbits
; Kernel info:
; codeLenInByte = 604
; TotalNumSgprs: 34
; NumVgprs: 8
; ScratchSize: 64
; MemoryBound: 0
; FloatMode: 240
; IeeeMode: 1
; LDSByteSize: 0 bytes/workgroup (compile time only)
; SGPRBlocks: 4
; VGPRBlocks: 0
; NumSGPRsForWavesPerEU: 34
; NumVGPRsForWavesPerEU: 8
; Occupancy: 16
; WaveLimiterHint : 0
; COMPUTE_PGM_RSRC2:SCRATCH_EN: 1
; COMPUTE_PGM_RSRC2:USER_SGPR: 13
; COMPUTE_PGM_RSRC2:TRAP_HANDLER: 0
; COMPUTE_PGM_RSRC2:TGID_X_EN: 1
; COMPUTE_PGM_RSRC2:TGID_Y_EN: 1
; COMPUTE_PGM_RSRC2:TGID_Z_EN: 1
; COMPUTE_PGM_RSRC2:TIDIG_COMP_CNT: 0
	.text
	.p2alignl 7, 3214868480
	.fill 96, 4, 3214868480
	.section	.AMDGPU.gpr_maximums,"",@progbits
	.set amdgpu.max_num_vgpr, 0
	.set amdgpu.max_num_agpr, 0
	.set amdgpu.max_num_sgpr, 34
	.text
	.type	__hip_cuid_2716715752f3e0d2,@object ; @__hip_cuid_2716715752f3e0d2
	.section	.bss,"aw",@nobits
	.globl	__hip_cuid_2716715752f3e0d2
__hip_cuid_2716715752f3e0d2:
	.byte	0                               ; 0x0
	.size	__hip_cuid_2716715752f3e0d2, 1

	.hidden	__oclc_ABI_version              ; @__oclc_ABI_version
	.type	__oclc_ABI_version,@object
	.section	.rodata,"a",@progbits
	.weak	__oclc_ABI_version
	.p2align	2, 0x0
__oclc_ABI_version:
	.long	600                             ; 0x258
	.size	__oclc_ABI_version, 4

	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.ident	"AMD clang version 20.0.0git (https://github.com/RadeonOpenCompute/llvm-project roc-7.1.1 25444 27682a16360e33e37c4f3cc6adf9a620733f8fe1)"
	.section	".note.GNU-stack","",@progbits
	.addrsig
	.addrsig_sym __hip_cuid_2716715752f3e0d2
	.amdgpu_metadata
---
amdhsa.kernels:
  - .args:
      - .address_space:  global
        .offset:         0
        .size:           8
        .value_kind:     global_buffer
      - .address_space:  global
        .offset:         8
        .size:           8
        .value_kind:     global_buffer
      - .address_space:  global
        .offset:         16
        .size:           8
        .value_kind:     global_buffer
      - .offset:         24
        .size:           4
        .value_kind:     hidden_block_count_x
      - .offset:         28
        .size:           4
        .value_kind:     hidden_block_count_y
      - .offset:         32
        .size:           4
        .value_kind:     hidden_block_count_z
      - .offset:         36
        .size:           2
        .value_kind:     hidden_group_size_x
      - .offset:         38
        .size:           2
        .value_kind:     hidden_group_size_y
      - .offset:         40
        .size:           2
        .value_kind:     hidden_group_size_z
      - .offset:         42
        .size:           2
        .value_kind:     hidden_remainder_x
      - .offset:         44
        .size:           2
        .value_kind:     hidden_remainder_y
      - .offset:         46
        .size:           2
        .value_kind:     hidden_remainder_z
      - .offset:         64
        .size:           8
        .value_kind:     hidden_global_offset_x
      - .offset:         72
        .size:           8
        .value_kind:     hidden_global_offset_y
      - .offset:         80
        .size:           8
        .value_kind:     hidden_global_offset_z
      - .offset:         88
        .size:           2
        .value_kind:     hidden_grid_dims
      - .offset:         104
        .size:           8
        .value_kind:     hidden_hostcall_buffer
      - .offset:         112
        .size:           8
        .value_kind:     hidden_multigrid_sync_arg
      - .offset:         120
        .size:           8
        .value_kind:     hidden_heap_v1
      - .offset:         128
        .size:           8
        .value_kind:     hidden_default_queue
      - .offset:         136
        .size:           8
        .value_kind:     hidden_completion_action
      - .offset:         224
        .size:           8
        .value_kind:     hidden_queue_ptr
    .group_segment_fixed_size: 0
    .kernarg_segment_align: 8
    .kernarg_segment_size: 280
    .language:       OpenCL C
    .language_version:
      - 2
      - 0
    .max_flat_workgroup_size: 1
    .name:           E
    .private_segment_fixed_size: 64
    .sgpr_count:     34
    .sgpr_spill_count: 0
    .symbol:         E.kd
    .uniform_work_group_size: 1
    .uses_dynamic_stack: false
    .vgpr_count:     8
    .vgpr_spill_count: 0
    .wavefront_size: 32
    .workgroup_processor_mode: 1
amdhsa.target:   amdgcn-amd-amdhsa--gfx1100
amdhsa.version:
  - 1
  - 2
...

	.end_amdgpu_metadata

union ast = {
    // SOP2 Instructions
    Inst_S_ADD_I32 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_SUB_U32 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_ADD_U32 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_AND_B32 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_CSELECT_B32 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_LSHR_B64 : (sgpr_idx, sgpr_src, sgpr_src),
    Inst_S_AND_NOT1_B32 : (sgpr_idx, sgpr_src, sgpr_src),

    // SOP1 Instructions
    Inst_S_MOV_B32 : (sgpr_idx, sgpr_src),
    Inst_S_MOV_B64 : (sgpr_idx, sgpr_src),
    Inst_S_AND_SAVEEXEC_B32 : (sgpr_idx, sgpr_src),

    // SOPC Instructions
    Inst_S_CMP_EQ_I32 : (sgpr_src, sgpr_src),
    Inst_S_CMP_LG_I32 : (sgpr_src, sgpr_src),
    Inst_S_BITCMP0_B32 : (sgpr_src, sgpr_src),

    // SOPP Instructions
    Inst_S_NOP : unit,
    Inst_S_CLAUSE : unit,
    Inst_S_DELAY_ALU : unit,
    Inst_S_WAITCNT : simm_16,
    Inst_S_BRANCH : simm_16,
    Inst_S_CBRANCH_SCC1 : simm_16,
    Inst_S_SENDMSG : simm_16,
    Inst_S_ENDPGM : unit,
    Inst_S_WAITCNT_VSCNT : simm_16,

    // VOP3SD Instructions
    Inst_V_ADD_CO_CI_U32_VOP3 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_ADD_CO_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src),
    Inst_V_MAD_U64_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_LSHLREV_B64 : (vgpr_idx, vop_src, vop_src),
    Inst_V_LSHL_ADD_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_ADD3_U32 : (vgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_CMP_LT_U32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_CMP_GT_I32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_CNDMASK_B32_VOP3 : (vgpr_idx, vop_src, vop_src, vop_src),

    // VOP2 Instructions
    Inst_V_CNDMASK_B32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_ADD_CO_CI_U32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_ASHRREV_I32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_ADD_NC_U32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_LSHLREV_B32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_AND_B32 : (vgpr_idx, vop_src, vop_src),

    // VOP1 Instructions
    Inst_V_MOV_B32 : (vgpr_idx, vop_src),

    // SMEM Instructions
    Inst_S_LOAD_B32 : (sbase, sgpr_idx, offset_21, sgpr_idx),
    Inst_S_LOAD_B64 : (sbase, sgpr_idx, offset_21, sgpr_idx),

    // SCRATCH Instructions
    Inst_SCRATCH_LOAD_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                              vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_SCRATCH_LOAD_B64 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                              vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_SCRATCH_STORE_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                               vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_SCRATCH_STORE_B64 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                               vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),

    // FLAT Instructions
    Inst_FLAT_LOAD_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                          vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_FLAT_STORE_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                           vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_FLAT_LOAD_B64 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                          vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_FLAT_STORE_B64 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                           vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),

    // GLOBAL Instructions
    Inst_GLOBAL_LOAD_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                             vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),
    Inst_GLOBAL_STORE_B32 : (mem_offset_12, flag_1, flag_1, flag_1, seg_2, opcode_8,
                              vgpr_idx, vgpr_idx, sgpr_idx, flag_1, vgpr_idx),

    // DS (Local Data Share) Instructions
    Inst_DS_READ_B32 : (vgpr_idx, vgpr_idx, offset_8),

    // MUBUF Instructions
    Inst_BUFFER_LOAD_B128 : (vgpr_idx, vgpr_idx, srsrc_5, soffset_8, mem_offset_12, flag_1, flag_1, flag_1, flag_1, flag_1),

    Inst_INVALID : unit
}

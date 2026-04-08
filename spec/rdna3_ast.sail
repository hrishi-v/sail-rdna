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

    // SOPP Instructions
    Inst_S_CLAUSE : unit,
    Inst_S_DELAY_ALU : unit,
    Inst_S_WAITCNT : bits(16),
    Inst_S_BRANCH : bits(16),
    Inst_S_ENDPGM : unit,

    // VOP3SD Instructions
    Inst_V_ADD_CO_CI_U32_VOP3 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_ADD_CO_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src),
    Inst_V_MAD_U64_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_LSHLREV_B64 : (vgpr_idx, vop_src, vop_src),
    Inst_V_LSHL_ADD_U32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_ADD3_U32 : (vgpr_idx, vop_src, vop_src, vop_src),
    Inst_V_CMP_LT_U32 : (vgpr_idx, vop_src, vop_src, vop_src),

    // VOP2 Instructions
    Inst_V_ADD_CO_CI_U32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_ASHRREV_I32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_ADD_NC_U32 : (vgpr_idx, vop_src, vop_src),
    Inst_V_LSHLREV_B32 : (vgpr_idx, vop_src, vop_src),

    // VOP1 Instructions
    Inst_V_MOV_B32 : (vgpr_idx, vop_src),

    // SMEM Instructions
    // sbase: bits(6) — 6-bit SGPR pair base (unique width, not sgpr_idx)
    Inst_S_LOAD_B32 : (bits(6), sgpr_idx, bits(21), sgpr_idx),
    Inst_S_LOAD_B64 : (bits(6), sgpr_idx, bits(21), sgpr_idx),

    // FLAT Instructions
    // fields: offset(12), dlc(1), glc(1), slc(1), seg(2), op(8),
    //         addr(vgpr_idx), data(vgpr_idx), saddr(sgpr_idx), sve(1), vdst(vgpr_idx)
    Inst_FLAT_LOAD_B32 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                          vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),
    Inst_FLAT_STORE_B32 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                           vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),
    Inst_FLAT_LOAD_B64 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                          vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),
    Inst_FLAT_STORE_B64 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                           vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),

    // GLOBAL Instructions (seg=01; saddr=0x7F → VGPR pair addr, else SGPR base + VGPR offset)
    Inst_GLOBAL_LOAD_B32 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                             vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),
    Inst_GLOBAL_STORE_B32 : (bits(12), bits(1), bits(1), bits(1), bits(2), BYTE,
                              vgpr_idx, vgpr_idx, sgpr_idx, bits(1), vgpr_idx),

    Inst_INVALID : unit
}

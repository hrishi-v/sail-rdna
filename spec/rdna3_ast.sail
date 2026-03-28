union ast = {
    // SOP2 Instructions
    Inst_S_ADD_I32 : (scalar_dst, scalar_src, scalar_src),
    Inst_S_SUB_U32 : (scalar_dst, scalar_src, scalar_src),
    Inst_S_ADD_U32 : (scalar_dst, scalar_src, scalar_src),
    Inst_S_CSELECT_B32 : (scalar_dst, scalar_src, scalar_src),
    Inst_S_LSHR_B64 : (scalar_dst, scalar_src, scalar_src),

    // SOP1 Instructions
    Inst_S_MOV_B32 : (scalar_dst, scalar_src),
    Inst_S_MOV_B64 : (scalar_dst, scalar_src),

    // SOPC Instructions
    Inst_S_CMP_EQ_I32 : (scalar_src, scalar_src),
    Inst_S_CMP_LG_I32 : (scalar_src, scalar_src),

    // SOPP Instructions
    Inst_S_WAITCNT : bits(16),
    Inst_S_ENDPGM : unit,

    // VOP2 Instructions
    Inst_V_ADD_NC_U32 : (vector_dst, vop_src, vop_src),

    // VOP1 Instructions
    Inst_V_MOV_B32 : (vector_dst, vop_src),

    // SMEM Instructions
    Inst_S_LOAD_B64 : (smem_base, smem_data, smem_offset, smem_soffset),

    // FLAT Instructions
    Inst_FLAT_LOAD_B32 : (flat_offset, flat_dlc_bit, flat_glc_bit,
                          flat_slc_bit, flat_seg, flat_op, flat_addr,
                          flat_data, flat_saddr, flat_sve_bit, flat_vdst),
    Inst_FLAT_STORE_B32 : (flat_offset, flat_dlc_bit, flat_glc_bit,
                          flat_slc_bit, flat_seg, flat_op, flat_addr,
                          flat_data, flat_saddr, flat_sve_bit, flat_vdst),

    Inst_INVALID : unit
}

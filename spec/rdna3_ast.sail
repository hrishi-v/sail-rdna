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
    Inst_S_ENDPGM : unit,

    // VOP2 Instructions
    Inst_V_ADD_NC_U32 : (vector_dst, vector_src, vop_src),

    // VOP1 Instructions
    Inst_V_MOV_B32 : (vector_dst, vop_src),

    // FLAT Instructions
    Inst_FLAT_LOAD_B32 : (flat_offset, flat_dlc_bit, flat_glc_bit,
                          flat_slc_bit, flat_seg, flat_op, flat_addr,
                          flat_data, flat_saddr, flat_sve_bit, flat_vdst),
    Inst_FLAT_STORE_B32 : (flat_offset, flat_dlc_bit, flat_glc_bit,
                          flat_slc_bit, flat_seg, flat_op, flat_addr,
                          flat_data, flat_saddr, flat_sve_bit, flat_vdst),

    Inst_INVALID : unit // Not specified
}

val inst_size : ast -> int
function inst_size inst = {
    match inst {
        Inst_FLAT_LOAD_B32(_, _, _, _, _, _, _, _, _, _, _) => 8,
        Inst_FLAT_STORE_B32(_, _, _, _, _, _, _, _, _, _, _) => 8,
        Inst_V_MOV_B32(_, src0) => if unsigned(src0) == 255 then { 8 } else { 4 },
        Inst_V_ADD_NC_U32(_, _, src0) => if unsigned(src0) == 255 then { 8 } else { 4 },
        _ => 4,
    }
}

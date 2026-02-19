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

    // Vector ALU Instructions
    // Inst_V_MOV_B32 : (, operand),
    // Inst_V_ADD_U32 : (, operand, operand),
    // Inst_V_ADD_U32 : (),

    Inst_INVALID : unit // Not specified
}
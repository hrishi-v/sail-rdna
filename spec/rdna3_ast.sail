union ast = {
    // Signed Scalar ALU Instructions
    Inst_S_ADD_I32 : (scalar_dst, scalar_src, scalar_src),

    // Binary Scalar ALU Instructions 
    Inst_S_MOV_B32 : (scalar_dst, scalar_src),
    
    // Unsigned Scalar ALU Instructions
    Inst_S_SUB_U32 : (scalar_dst, scalar_src, scalar_src),
    Inst_S_ADD_U32 : (scalar_dst, scalar_src, scalar_src),

    // Vector ALU Instructions
    // Inst_V_MOV_B32 : (, operand),
    // Inst_V_ADD_U32 : (, operand, operand),
    // Inst_V_ADD_U32 : (),

    Inst_INVALID : unit // Not specified
}
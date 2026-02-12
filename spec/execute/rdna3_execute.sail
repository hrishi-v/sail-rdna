val execute : ast -> unit
function execute(inst) = {
    match inst {
        // SOP2
        Inst_S_ADD_U32(d, s0, s1) => s_add_u32(d, s0, s1),
        Inst_S_SUB_U32(d, s0, s1) => s_sub_u32(d, s0, s1),

        // SOP1
        Inst_S_MOV_B32(d, s0) => s_mov_b32(d, s0),
        Inst_INVALID() => print("Error: Executing invalid instruction"),
        _ => print("Error: Unimplemented instruction execution")
    }
}
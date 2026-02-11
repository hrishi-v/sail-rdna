$include "rdna3_execute_scalar.sail"

val execute : ast -> unit
function execute(inst) = {
    match inst {
        Inst_S_ADD_U32(d, s0, s1) => s_add_u32(d, s0, s1),
        Inst_INVALID() => print("Error: Executing invalid instruction"),
        _ => print("Error: Unimplemented instruction execution")
    }
}
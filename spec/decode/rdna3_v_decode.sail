val vop2_decode : bits(32) -> ast
function vop2_decode(instr) = {
    let opc = instr[30..25];
    let vdst = instr[24..17];
    let vsrc = instr[16..9];
    let src = instr[8..0];
    match opc {
        // VOP2 Instructions
        0b100101 => Inst_V_ADD_NC_U32(vdst, vsrc, src),
        _ => Inst_INVALID()
    }
}

val vop1_decode : bits(32) -> ast
function vop1_decode(instr) = {
    let vdst = instr[24..17]; 
    let opc   = instr[16..9];  
    let src0 = instr[8..0];

    match opc {
        0b00000001 => Inst_V_MOV_B32(vdst, src0),
        _          => Inst_INVALID()
    }
}
val sop2_decode : bits(32) -> ast
function sop2_decode(instr) = {
    let opc = instr[29..23];
    let sdst = instr[22..16];
    let ssrc1 = instr[15..8];
    let ssrc0 = instr[7..0];
    match opc {
        0b0000000 => Inst_S_ADD_U32(sdst, ssrc0, ssrc1),
        0b0000001 => Inst_S_SUB_U32(sdst, ssrc0, ssrc1),
        _ => Inst_INVALID()
    }
}
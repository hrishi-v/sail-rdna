val flat_decode : QWORD -> ast
function flat_decode instr = {
    let offset = instr[11..0];

    let dlc = instr[12..12];
    let glc = instr[13..13];
    let slc = instr[14..14];
    let seg = instr[17..16];
    let opc = instr[25..18];
    let addr = instr[39..32];
    let data = instr[47..40];
    let saddr = instr[54..48];

    let sve = instr[55..55];
    let vdst = instr[63..56];

    match opc {
        0b00010100 => Inst_FLAT_LOAD_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst),
        0b00011010 => Inst_FLAT_STORE_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst),
        _ => Inst_INVALID(),
    }
}

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

    match (seg, opc) {
        // FLAT (seg=00)
        (0b00, 0b00010100) => Inst_FLAT_LOAD_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 20
        (0b00, 0b00011010) => Inst_FLAT_STORE_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 26
        (0b00, 0b00010101) => Inst_FLAT_LOAD_B64(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 21
        (0b00, 0b00011011) => Inst_FLAT_STORE_B64(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 27
        // GLOBAL (seg=10)
        (0b10, 0b00010100) => Inst_GLOBAL_LOAD_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 20
        (0b10, 0b00011010) => Inst_GLOBAL_STORE_B32(offset, dlc, glc, slc, seg, opc, addr, data, saddr, sve, vdst), // 26
        _ => Inst_INVALID(),
    }
}

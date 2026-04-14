val mubuf_decode : QWORD -> ast
function mubuf_decode instr = {
    let offset : bits(12) = instr[11..0];
    let slc : bits(1) = instr[12..12];
    let dlc : bits(1) = instr[13..13];
    let glc : bits(1) = instr[14..14];
    let op : bits(8) = instr[25..18];
    let vaddr : vgpr_idx = instr[39..32];
    let vdata : vgpr_idx = instr[47..40];
    let srsrc : bits(5) = instr[52..48];
    let tfe : bits(1) = instr[53..53];
    let offen : bits(1) = instr[54..54];
    let idxen : bits(1) = instr[55..55];
    let soffset : bits(8) = instr[63..56];

    match op {
        0b00010111 => Inst_BUFFER_LOAD_B128(vdata, vaddr, srsrc, soffset, offset, offen, idxen, glc, slc, dlc),
        _ => Inst_INVALID()
    }
}

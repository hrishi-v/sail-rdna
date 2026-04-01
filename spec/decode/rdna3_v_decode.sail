val vop3_decode : QWORD -> ast
function vop3_decode instr = {
    let neg = instr[63..61];
    let omod = instr[60..59];
    let src2 = instr[58..50];
    let src1 = instr[49..41];
    let src0 = instr[40..32];

    let encoding = instr[31..26];
    let opc = instr[25..16];
    // VOP3A fields
    let cm = instr[15..15];
    let opsel = instr[14..11];
    let abs = instr[10..8];
    let vdst = instr[7..0];
    // VOP3SD extra field (replaces cm/opsel/abs); valid values all fit in 7 bits (max 127)
    let sdst : sgpr_idx = instr[14..8];

    let vsrc = instr[16..9];
    let src = instr[8..0];

    match opc {
        0b0100100101 => Inst_V_ADD_NC_U32(vdst, src1, src0),
        // VOP3SD
        0b1011111110 => Inst_V_MAD_U64_U32(vdst, sdst, src0, src1, src2), // 766, ISA §16.12
        _ => {
            print("VOP3 Decode Error: Unknown Opcode 0x");
            Inst_INVALID()
        },
    }
}

val vop2_decode : DWORD -> ast
function vop2_decode instr = {
    let opc = instr[30..25];
    let vdst = instr[24..17];
    let vsrc = instr[16..9];
    let src = instr[8..0];
    match opc {
        // VOP2 Instructions
        0b100101 => {
            Inst_V_ADD_NC_U32(vdst, 0b1 @ vsrc, src)
        },
        _ => Inst_INVALID(),
    }
}

val vop1_decode : DWORD -> ast
function vop1_decode instr = {
    let vdst = instr[24..17];
    let opc = instr[16..9];
    let src0 = instr[8..0];

    match opc {
        0b00000001 => Inst_V_MOV_B32(vdst, src0),
        _ => Inst_INVALID(),
    }
}

val vopc_decode : DWORD -> ast
function vopc_decode instr = {
    Inst_INVALID()
}

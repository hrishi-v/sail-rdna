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
        // VOP3
        0b0100011000 => Inst_V_LSHLREV_B32(vdst, src0, src1), // 280, ISA §16.12
        0b0100100101 => Inst_V_ADD_NC_U32(vdst, src0, src1), // 293 - same implementation, different encoding!
        // VOP3SD
        0b0100100000 => Inst_V_ADD_CO_CI_U32_VOP3(vdst, sdst, src0, src1, src2), // 288, ISA §16.12
        0b1001000110 => Inst_V_LSHL_ADD_U32(vdst, sdst, src0, src1, src2), // 582, ISA §16.12
        0b1011111110 => Inst_V_MAD_U64_U32(vdst, sdst, src0, src1, src2), // 766, ISA §16.12
        0b1100000000 => Inst_V_ADD_CO_U32(vdst, sdst, src0, src1), // 768, ISA §16.12
        0b1100111100 => Inst_V_LSHLREV_B64(vdst, src0, src1), // 828, ISA §16.12
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
        // VOP2
        0b011000 => Inst_V_LSHLREV_B32(vdst, 0b1 @ vsrc, src), // 24
        0b011010 => Inst_V_ASHRREV_I32(vdst, 0b1 @ vsrc, src), // 26
        0b100000 => Inst_V_ADD_CO_CI_U32(vdst, 0b1 @ vsrc, src), // 32
        0b100101 => Inst_V_ADD_NC_U32(vdst, 0b1 @ vsrc, src), // 37
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

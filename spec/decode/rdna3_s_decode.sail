val sop2_decode : DWORD -> ast
function sop2_decode instr = {
    let opc = instr[29..23];
    let sdst = instr[22..16];
    let ssrc1 = instr[15..8];
    let ssrc0 = instr[7..0];
    match opc {
        0b0000000 => Inst_S_ADD_U32(sdst, ssrc0, ssrc1),
        0b0000001 => Inst_S_SUB_U32(sdst, ssrc0, ssrc1),
        //0b0001010 => Inst_S_LSHR_B32
        0b0001011 => Inst_S_LSHR_B64(sdst, ssrc0, ssrc1),
        0b0110000 => Inst_S_CSELECT_B32(sdst, ssrc0, ssrc1),
        // 0b0110001 => Inst_S_CSELECT_B64(sdst, ssrc0, ssrc1),
        _ => Inst_INVALID(),
    }
}

val sop1_decode : DWORD -> ast
function sop1_decode instr = {
    let sdst = instr[22..16];
    let opc = instr[15..8];
    let ssrc0 = instr[7..0];
    match opc {
        0b00000000 => Inst_S_MOV_B32(sdst, ssrc0),
        0b00000001 => Inst_S_MOV_B64(sdst, ssrc0),
        _ => Inst_INVALID(),
    }
}

val sopc_decode : DWORD -> ast
function sopc_decode instr = {
    let opc = instr[22..16];
    let ssrc1 = instr[15..8];
    let ssrc0 = instr[7..0];
    match opc {
        0b0000000 => Inst_S_CMP_EQ_I32(ssrc0, ssrc1),
        0b0000001 => Inst_S_CMP_LG_I32(ssrc0, ssrc1),
        _ => Inst_INVALID(),
    }
}

val sopp_decode : DWORD -> ast
function sopp_decode instr = {
    let opc = instr[22..16];
    let simm16 = instr[15..0];

    match opc {
        0b0110000 => Inst_S_ENDPGM(),
        _ => Inst_INVALID(),
    }
}

// val smem_decode : QWORD -> ast = {
//     let op        = qword_instr[25..18];
//     let sdst      = qword_instr[12..6];
//     let sbase_raw = qword_instr[5..0];
//     let sbase     = sbase_raw << 1;
//     let offset    = qword_instr[52..32];
//     if (op == 0b00000001) then {
//         s_load_b64(sbase, sdst, offset)
//     } else {
//         Inst_INVALID()
//     }
// }

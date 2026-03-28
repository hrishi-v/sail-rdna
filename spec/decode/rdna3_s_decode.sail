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
        0b0001001 => Inst_S_WAITCNT(simm16),
        0b0110000 => Inst_S_ENDPGM(),
        _ => Inst_INVALID(),
    }
}

val smem_decode : QWORD -> ast
function smem_decode instr = {
    let sbase = instr[5..0];
    let sdata = instr[12..6];
    let dlc = instr[14..14];
    let glc = instr[16..16];
    let opc = instr[25..18];
    let encoding = instr[31..26];

    let offset = instr[52..32];
    let soffset = instr[63..57];

    match opc {
        0b00000001 => Inst_S_LOAD_B64(sbase, sdata, offset, soffset),
        _ => Inst_INVALID(),
    }
}

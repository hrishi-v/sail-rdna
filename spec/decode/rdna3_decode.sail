val decode : DWORD -> ast
function decode instr = {
    if instr[31..31] == 0b0 then {
        if instr[30..25] == 0b111111 then {
            vop1_decode(instr)
        } else {
            if instr[30..25] == 0b111110 then {
                vopc_decode(instr)
            } else {
                vop2_decode(instr)
            }
        }
    } else {
        if instr[31..26] == 0b110101 then {
            let w1 = fetch_inst(PC);
            PC = PC + 4;
            vop3_decode(w1 @ instr)
        } else {
            if instr[31..26] == 0b111101 then {
                let w1 = fetch_inst(PC);
                PC = PC + 4;
                smem_decode(w1 @ instr)
            } else {
                if instr[31..26] == 0b110111 then {
                    let w1 = fetch_inst(PC);
                    PC = PC + 4;
                    flat_decode(w1 @ instr)
                } else {
                    if instr[31..30] == 0b10 then {
                        if instr[29..23] == 0b1111101 then {
                            sop1_decode(instr)
                        } else {
                            if instr[29..23] == 0b1111110 then {
                                sopc_decode(instr)
                            } else {
                                if instr[29..23] == 0b1111111 then {
                                    sopp_decode(instr)
                                } else {
                                    sop2_decode(instr)
                                }
                            }
                        }
                    } else {
                        Inst_INVALID()
                    }
                }
            }
        }
    }
}

val decode : bits(32) -> ast
function decode(instr) = {
    if (instr[31..30] == 0b10) then {
        if (instr[29..23] == 0b1111101) then {
            sop1_decode(instr)
        } else if (instr[29..23] == 0b1111110) then {
            sopc_decode(instr)
        } else if (instr[29..23] == 0b1111111) then  {
            sopp_decode(instr)
        } else if (instr[29..28] == 0b11) then {
            sopk_decode(instr)
        } else {
            sop2_decode(instr)
        }
    }
    // } else if (instr[31] == 0b0) then {
    //     v_decode(instr)
    // }
}
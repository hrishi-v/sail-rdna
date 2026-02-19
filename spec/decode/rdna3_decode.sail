val decode : bits(32) -> ast
function decode(instr) = {
    if (instr[31..30] == 0b10) then {
        if (instr[29..23] == 0b1111101) then {
            sop1_decode(instr)
        } 
        else if (instr[29..23] == 0b1111110) then {
            sopc_decode(instr) // SOPC not implemented yet
        } 
        else if (instr[29..23] == 0b1111111) then {
            Inst_INVALID() // SOPP not implemented yet
        } 
        else if (instr[29..28] == 0b11) then {
            Inst_INVALID() // SOPK not implemented yet
        } 
        else {
            sop2_decode(instr)
        }
    } else {
        Inst_INVALID()
    }
}
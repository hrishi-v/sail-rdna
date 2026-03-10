val decode : (DWORD, QWORD) -> ast
function decode(instr, pc) = {
    
    if (instr[31..25] == 0b0111111) then {
        vop1_decode(instr) 
    } else if (instr[31..31] == 0b0) then {
        vop2_decode(instr)
    }
    else if (instr[31..30] == 0b10) then {
        if (instr[29..23] == 0b1111101) then {
            sop1_decode(instr)
        } 
        else if (instr[29..23] == 0b1111110) then {
            sopc_decode(instr)
        } 
        else if (instr[29..23] == 0b1111111) then {
            sopp_decode(instr)
        } 
        else if (instr[29..28] == 0b11) then {
            Inst_INVALID() // SOPK not implemented yet
        } 
        else {
            sop2_decode(instr)
        }
    } 
    else if (instr[31..26] == 0b110111) then {
        
        let next_dword = fetch_inst(pc + 4); 
        let full_qword : QWORD = next_dword @ instr; 
        
        flat_decode(full_qword)
    } else if (instr[31..26] == 0b111101) then {
        let next_dword = fetch_inst(pc + 4);
        let full_qword : QWORD = next_dword @ instr;

        smem_decode(full_qword)
    }
    else {
        Inst_INVALID()
    } 
}
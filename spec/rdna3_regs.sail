register PC : QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)

// Read SGPR registers
val rSGPR : scalar_src -> DWORD
function rSGPR(id) = {
    let idx = unsigned(id); 
    if (idx <= 105) then {
        SGPR[idx]
    }
    else {
        0x00000000
    }
}

// Write SGPR registers
val wSGPR : (scalar_dst, DWORD) -> unit
  function wSGPR(id, value) = {
    let idx = unsigned(id);
    if idx <= 107 then {
      SGPR[idx] = value
    }
  }

// Read VCC register, specific SGPRs 106 and 107, return QWORD
val rVCC : unit -> QWORD
function rVCC() = {
  SGPR[107] @ SGPR[106]
}

// Write VCC register, specific SGPRs 106 and 107
val wVCC : QWORD -> unit
function wVCC(value) = {
  SGPR[107] = value[63..32];
  SGPR[106] = value[31..0];
}

val rSCC : unit -> bit
function rSCC() = {
  SCC[0]
}

val wSCC : bit -> unit
function wSCC(value) = {
  SCC[0] = value
}
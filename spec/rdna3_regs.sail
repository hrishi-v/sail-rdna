$include "rdna3_types.sail"

register PC : QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)

val rSGPR : reg_id -> DWORD
function rSGPR(id) = {
    let idx = unsigned(id); 
    if (idx <= 105) then {
        SGPR[idx]
    }
    else if (idx == 106) then {
        SGPR[106]
    }
    else if (idx == 107) then {
        SGPR[107]
    }
    else {
        0x00000000
    }
}

val wSGPR : (reg_id, DWORD) -> unit
  function wSGPR(id, value) = {
    let idx = unsigned(id);
    if idx <= 107 then {
      SGPR[idx] = value
    }
  }
  
val rVCC : unit -> QWORD
function rVCC() = {
  SGPR[107] @ SGPR[106]
}

val wVCC : QWORD -> unit
function wVCC(value) = {
  SGPR[107] = value[63..32];
  SGPR[106] = value[31..0];
}
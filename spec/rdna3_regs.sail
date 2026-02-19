register PC : QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)

// Read SGPR registers
val rSGPR : scalar_src -> DWORD
function rSGPR(id) = {
    let idx = unsigned(id); 
    if (idx <= 107) then {
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

val read_scalar_source : scalar_src -> DWORD
function read_scalar_source(id) = {
  let idx = unsigned(id);

  // SGPR Registers
  if idx <= 107 then {
    rSGPR(id);
  // Integer Literal Constants (128-192)
  } else if idx >= 128 & idx <= 192 then {
    let val_int = idx - 128;
    get_slice_int(32, val_int, 0);
  } else {
    0x00000000
  }
}

// Special Registers

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
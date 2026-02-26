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
    rSGPR(id)
  // Integer Literal Constants (128-192)
  } else if idx >= 128 & idx <= 192 then {
    let val_int = idx - 128;
    get_slice_int(32, val_int, 0)
  } else {
    0x00000000
  }
}

val write_scalar_dst64 : (scalar_dst, QWORD) -> unit
function write_scalar_dst64(id, value) = {
  let idx = unsigned(id);
  
  let lower32 = value[31..0];
  let upper32 = value[63..32];

  let id_plus_1 : scalar_dst = get_slice_int(7, idx + 1, 0);

  wSGPR(id, lower32);
  wSGPR(id_plus_1, upper32);
}


val read_scalar_source64 : scalar_src -> QWORD
function read_scalar_source64(id) = {
  let idx = unsigned(id);

  if idx <= 106 then {
    let id_base   : scalar_src = get_slice_int(8, idx, 0);
    let id_plus_1 : scalar_src = get_slice_int(8, idx + 1, 0);
    
    read_scalar_source(id_plus_1) @ read_scalar_source(id_base)
  } 
  else if idx >= 128 then {
    0x00000000 @ read_scalar_source(id)
  } 
  else {
    0x0000000000000000 
  }
}

val rSCC : unit -> bit
function rSCC() = {
  SCC[0]
}

val wSCC : bit -> unit
function wSCC(value) = {
  SCC[0] = value
}

val set_pc : QWORD -> unit
function set_pc(start_addr) = {
    PC = start_addr
}

val get_halt_flag : unit -> bool
function get_halt_flag() = {
  halt_flag == 0b1
}

val set_halt_flag : unit -> unit
function set_halt_flag() = {
    halt_flag = 0b1
}

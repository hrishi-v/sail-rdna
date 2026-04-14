
val check_sgpr_plq : int -> unit

// Read SGPR registers, when a physical SGPR index is guaranteed!
val rSGPR : sgpr_idx -> DWORD
function rSGPR id = {
    let idx = unsigned(id);
    if idx <= 107 then {
        check_sgpr_plq(idx);
        SGPR[idx]
    } else { 0x00000000 }
}

// Write SGPR registers
val wSGPR : (sgpr_idx, DWORD) -> unit
function wSGPR(id, value) = {
    let idx = unsigned(id);
    if idx <= 107 then {
        SGPR[idx] = value
    } else {
        if idx == 124 then {
            M0 = value
        } else {
            if idx == 126 then {
                EXEC_LO = value
            } else {
                if idx == 127 then {
                    EXEC_HI = value
                }
            }
        }
    }
}

val read_common_source : int -> DWORD
function read_common_source idx = {
    if idx == 255 then {
        let literal = fetch_inst(PC);
        PC = PC + 4;
        literal
    } else {
        if idx >= 0 & idx <= 107 then {
            check_sgpr_plq(idx);
            SGPR[idx]
        } else {
            if idx >= 108 & idx <= 123 then { 0x00000000 } else {
                if idx == 124 then { M0 } else {
                    if idx == 125 then { 0x00000000 } else {
                        if idx == 126 then { EXEC_LO } else {
                            if idx == 127 then { EXEC_HI } else {
                                if idx == 128 then { 0x00000000 } else {
                                    if idx >= 129 & idx <= 192 then {
                                        get_slice_int(32, idx - 128, 0)
                                    } else {
                                        if idx >= 193 & idx <= 208 then {
                                            get_slice_int(32, 192 - idx, 0)
                                        } else {
                                            if idx == 240 then { 0x3f000000 } else {
                                                if idx == 241 then { 0xbf000000 } else {
                                                    if idx == 242 then { 0x3f800000 } else {
                                                        if idx == 243 then { 0xbf800000 } else {
                                                            if idx == 244 then { 0x40000000 } else {
                                                                if idx == 245 then { 0xc0000000 } else {
                                                                    if idx == 246 then { 0x40800000 } else {
                                                                        if idx == 247 then { 0xc0800000 } else {
                                                                            if idx == 248 then { 0x3e22f983 } else {
                                                                                0x00000000
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

val write_scalar_dst64 : (sgpr_idx, QWORD) -> unit
function write_scalar_dst64(id, value) = {
    let idx = unsigned(id);

    let lower32 = value[31..0];
    let upper32 = value[63..32];

    let id_plus_1 : sgpr_idx = get_slice_int(7, idx + 1, 0);

    wSGPR(id, lower32);
    wSGPR(id_plus_1, upper32)
}

function check_sgpr_plq sgpr_n = {
    foreach (i from 0 to 15) {
        if i < unsigned(PLQ_COUNT) then {
            let dst_n = unsigned(PLQ_DST[i]);
            let is_base = dst_n == sgpr_n;
            let is_upper = PLQ_NDW[i] == 0b1 & dst_n + 1 == sgpr_n;
            if is_base | is_upper then {
                if unsigned(CYCLE_COUNT) < unsigned(PLQ_READY[i]) then {
                    print(
                        "[DIAGNOSTIC] Load result used without synchronisation primitives. This may return stale data on bare metal. Use s_waitcnt to avoid stale loads.\n",
                    )
                }
            }
        }
    }
}

val read_scalar_source64 : sgpr_src -> QWORD
function read_scalar_source64 id = {
    let idx = unsigned(id);

    if idx <= 106 then {
        let id_base : sgpr_src = get_slice_int(8, idx, 0);
        let id_plus_1 : sgpr_src = get_slice_int(8, idx + 1, 0);

        read_common_source(unsigned(id_plus_1)) @ read_common_source(unsigned(id_base))
    } else {
        if idx >= 128 then {
            0x00000000 @ read_common_source(unsigned(id))
        } else { 0x0000000000000000 }
    }
}

val rSCC : unit -> bit
function rSCC () = {
    SCC[0]
}

val wSCC : bit -> unit
function wSCC value = {
    SCC[0] = value
}

val get_halt_flag : unit -> bool
function get_halt_flag () = {
    halt_flag == 0b1
}

val set_halt_flag : unit -> unit
function set_halt_flag () = {
    halt_flag = 0b1
}

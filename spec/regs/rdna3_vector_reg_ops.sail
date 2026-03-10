
// Read VCC register, specific SGPRs 106 and 107, return QWORD
val rVCC : unit -> QWORD
function rVCC () = {
    let vcc_lo = SGPR[106];
    let vcc_hi = SGPR[107];
    vcc_hi @ vcc_lo
}

// Write VCC register, specific SGPRs 106 and 107
val wVCC : QWORD -> unit
function wVCC value = {
    SGPR[107] = value[63..32];
    SGPR[106] = value[31..0];
    if value == 0x0000000000000000 then {
        VCCZ = 0b1
    } else {
        VCCZ = 0b0
    }
}

// Read from a Vector register, returning a lane-specific value
val rVGPR : (vector_src, vector_lane_id) -> DWORD
function rVGPR(reg_id, lane_id) = {
    let reg_idx = unsigned(reg_id);
    let lane_idx = unsigned(lane_id);
    if reg_idx < 256 & lane_idx <= 31 then {
        VGPR[reg_idx][lane_idx]
    } else { 0x00000000 }
}

// Write VGPR registers
val wVGPR : (vector_dst, vector_lane_id, DWORD) -> unit
function wVGPR(reg_id, lane_id, value) = {
    let reg_idx = unsigned(reg_id);
    let lane_idx = unsigned(lane_id);

    if reg_idx <= 255 & lane_idx <= 31 then {
        VGPR[reg_idx][lane_idx] = value
    }
}

// Route the VGPR Instructions
val read_vector_source : (bits(9), vector_lane_id) -> DWORD
function read_vector_source(src, lane_id) = {
    let idx = unsigned(src);

    if idx < 256 then {
        // reading from predefined operand (e.g. 0.5, pi)
        read_common_source(idx)
    } else {
        if idx >= 256 & idx <= 511 then {
            // reading from a VGPR
            let v_reg = get_slice_int(8, idx - 256, 0);
            rVGPR(v_reg, lane_id)
        } else { 0x00000000 }
    }
}

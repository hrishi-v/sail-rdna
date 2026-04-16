
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

val check_vgpr_vmq : int -> unit
function check_vgpr_vmq reg_idx = {
    if IN_EXECUTE == 0b1 & reg_idx >= 0 & reg_idx < 256 then {
        if VMQ_PENDING[reg_idx] == 0b1 then {
            print("[HAZARD] read of v");
            print_int("", reg_idx);
            print(" with pending VMEM load — missing s_waitcnt vmcnt(0)\n")
        }
    }
}

val vmem_mark_pending : vgpr_idx -> unit
function vmem_mark_pending vdst = {
    let idx = unsigned(vdst);
    if idx < 256 then {
        VMQ_PENDING[idx] = 0b1
    }
}

val vmem_issue_load : vgpr_idx -> unit
function vmem_issue_load vdst = {
    if unsigned(VMCNT) >= 63 then {
        print("[HAZARD] vmcnt overflow: 64th VMEM load issued without s_waitcnt. Hardware counter would wrap to 0.\n")
    };
    VMCNT = VMCNT + 1;
    let idx = unsigned(vdst);
    if idx < 256 then {
        VMQ_PENDING[idx] = 0b1
    }
}

// Read from a Vector register, returning a lane-specific value
val rVGPR : (vgpr_idx, lane_id) -> DWORD
function rVGPR(reg_id, lane_id) = {
    let reg_idx = unsigned(reg_id);
    let lane_idx = unsigned(lane_id);
    if reg_idx < 256 & lane_idx <= 31 then {
        check_vgpr_vmq(reg_idx);
        VGPR[reg_idx][lane_idx]
    } else { 0x00000000 }
}

// Write VGPR registers
val wVGPR : (vgpr_idx, lane_id, DWORD) -> unit
function wVGPR(reg_id, lane_id, value) = {
    let reg_idx = unsigned(reg_id);
    let lane_idx = unsigned(lane_id);

    if reg_idx <= 255 & lane_idx <= 31 then {
        VGPR[reg_idx][lane_idx] = value
    }
}

val vmem_push_vlq : vgpr_idx -> unit
function vmem_push_vlq vdst = {
    let q_idx = unsigned(VLQ_COUNT);
    if q_idx < 128 then {
        VLQ_DST[q_idx] = vdst;
        foreach (lane from 0 to 31) {
            VLQ_VAL[q_idx][lane] = VLQ_STAGE[lane]
        };
        VLQ_COUNT = VLQ_COUNT + 1
    }
}

val vmem_flush_vlq : unit -> unit
function vmem_flush_vlq () = {
    foreach (entry from 0 to 127) {
        if entry < unsigned(VLQ_COUNT) then {
            let dst : vgpr_idx = VLQ_DST[entry];
            foreach (lane from 0 to 31) {
                let lane_bv = get_slice_int(5, lane, 0);
                wVGPR(dst, lane_bv, VLQ_VAL[entry][lane])
            }
        }
    };
    VLQ_COUNT = 0b0000000
}

// Route the VGPR Instructions
val read_vector_source : (vop_src, lane_id) -> DWORD
function read_vector_source(src, lane_id) = {
    let idx = unsigned(src);

    if idx == 255 then {
        let literal = fetch_inst(PC);
        PC = PC + 4;
        literal
    } else {
        if idx < 256 then {
            read_common_source(idx)
        } else {
            if idx >= 256 & idx <= 511 then {
                let v_reg = get_slice_int(8, idx - 256, 0);
                rVGPR(v_reg, lane_id)
            } else { 0x00000000 }
        }
    }
}

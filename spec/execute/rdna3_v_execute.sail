// VOP2 Instructions

val v_add_nc_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_add_nc_u32(vdst, src1, src0) = {
    // Pre-read scalar/literal sources once — same value for all lanes.
    // read_vector_source handles literal fetch and PC advancement when src == 255.
    let op0_common : DWORD = if unsigned(src0) <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if unsigned(src1) <= 255 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if unsigned(src0) <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, unsigned(src0) - 256, 0), lane_bv)
            };
            let op1 = if unsigned(src1) <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, unsigned(src1) - 256, 0), lane_bv)
            };
            let res = unsigned(op0) + unsigned(op1);
            results[lane] = get_slice_int(32, res, 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, results[lane])
        }
    }
}

// VOP1 Instructions

val v_mov_b32 : (vgpr_idx, vop_src) -> unit
function v_mov_b32(vdst, src0) = {
    let val_to_move = read_vector_source(src0, 0b00000);

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, val_to_move)
        }
    }
}

// VOP3SD Instructions

val v_mad_u64_u32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_mad_u64_u32(vdst, sdst, src0, src1, src2) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);
    let src2_u = unsigned(src2);

    let op0_common : DWORD = if src0_u < 256 then { read_vector_source(src0, 0b00000) } else { 0x00000000 };
    let op1_common : DWORD = if src1_u < 256 then { read_vector_source(src1, 0b00000) } else { 0x00000000 };

    var results_lo : vector(32, dec, bits(32)) = undefined;
    var results_hi : vector(32, dec, bits(32)) = undefined;
    var carry : bits(32) = 0x00000000;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 : DWORD = if src0_u < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 : DWORD = if src1_u < 256 then { op1_common } else {
                rVGPR(get_slice_int(8, src1_u - 256, 0), lane_bv)
            };
            let src2_base : bits(8) = get_slice_int(8, src2_u - 256, 0);
            let addend_lo : DWORD = rVGPR(src2_base, lane_bv);
            let addend_hi : DWORD = rVGPR(src2_base + 0x01, lane_bv);
            let addend : QWORD = addend_hi @ addend_lo;

            let product : QWORD = get_slice_int(64, unsigned(op0) * unsigned(op1), 0);
            let result : bits(65) = (0b0 @ product) + (0b0 @ addend);

            results_lo[lane] = result[31..0];
            results_hi[lane] = result[63..32];
            carry[lane..lane] = result[64..64]
        } else {
            results_lo[lane] = rVGPR(vdst, lane_bv);
            results_hi[lane] = rVGPR(vdst + 0x01, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, results_lo[lane]);
            wVGPR(vdst + 0x01, lane_bv, results_hi[lane])
        }
    };

    wSGPR(sdst[6..0], carry)
}
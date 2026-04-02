// VOP2 Instructions

val v_ashrrev_i32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_ashrrev_i32(vdst, vsrc, src0) = {
    // src0 = shift amount (SRC0, flexible: scalar/constant/VGPR)
    // vsrc = value to shift (VSRC1, typically VGPR in VOP2 but vop_src allows scalar too)
    let op0_common : DWORD = if unsigned(src0) < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if unsigned(vsrc) < 256 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let shift_src : DWORD = if unsigned(src0) < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, unsigned(src0) - 256, 0), lane_bv)
            };
            let value : DWORD = if unsigned(vsrc) < 256 then { op1_common } else {
                rVGPR(get_slice_int(8, unsigned(vsrc) - 256, 0), lane_bv)
            };
            let shift_amt : int = unsigned(shift_src[4..0]);
            let result : DWORD = get_slice_int(32, shr_int(signed(value), shift_amt), 0);
            wVGPR(vdst, lane_bv, result)
        }
    }
}

val v_add_nc_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_add_nc_u32(vdst, vsrc, src0) = {
    let op0_common : DWORD = if unsigned(src0) <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if unsigned(vsrc) <= 255 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if unsigned(src0) <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, unsigned(src0) - 256, 0), lane_bv)
            };
            let op1 = if unsigned(vsrc) <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, unsigned(vsrc) - 256, 0), lane_bv)
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

val v_add_co_ci_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_add_co_ci_u32(vdst, vsrc, src0) = {
    let op0_common : DWORD = if unsigned(src0) <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if unsigned(vsrc) <= 255 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;
    let carry_in : bits(32) = rVCC()[31..0];
    var carry_out : bits(32) = 0x00000000;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if unsigned(src0) <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, unsigned(src0) - 256, 0), lane_bv)
            };
            let op1 = if unsigned(vsrc) <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, unsigned(vsrc) - 256, 0), lane_bv)
            };
            let ci_bit : bits(1) = carry_in[lane..lane];
            let tmp : bits(33) = (0b0 @ op0) + (0b0 @ op1) + (0x00000000 @ ci_bit);
            results[lane] = tmp[31..0];
            carry_out[lane..lane] = tmp[32..32]
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, results[lane])
        }
    };

    wVCC(rVCC()[63..32] @ carry_out)
}

val v_add_co_ci_u32_vop3 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_add_co_ci_u32_vop3(vdst, carry_dst, src0, src1, src2) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);

    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u <= 255 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };

    // carry-in is always an SGPR (src2 < 256), safe to pre-read outside the loop
    let carry_in : bits(32) = read_vector_source(src2, 0b00000);

    var results : vector(32, dec, bits(32)) = undefined;
    var carry_out : bits(32) = 0x00000000;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 : DWORD = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 : DWORD = if src1_u <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, src1_u - 256, 0), lane_bv)
            };
            let ci_bit : bits(1) = carry_in[lane..lane];
            let tmp : bits(33) = (0b0 @ op0) + (0b0 @ op1) + (0x00000000 @ ci_bit);
            results[lane] = tmp[31..0];
            carry_out[lane..lane] = tmp[32..32]
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, results[lane])
        }
    };

    wSGPR(carry_dst, carry_out)
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

// VOP3 Instructions
val v_lshlrev_b64 : (vgpr_idx, vop_src, vop_src) -> unit
function v_lshlrev_b64(vdst, src0, src1) = {
    // src0 = shift amount (lower 6 bits used), src1 = 64-bit source (VGPR pair or scalar pair)
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };

    let op1_common : QWORD = if src1_u < 256 then {
        read_scalar_source64(get_slice_int(8, src1_u, 0))
    } else { 0x0000000000000000 };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let shift_src : DWORD = if src0_u < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let shift_amt : int = unsigned(shift_src[5..0]);

            let value : QWORD = if src1_u < 256 then { op1_common } else {
                let src1_base : bits(8) = get_slice_int(8, src1_u - 256, 0);
                rVGPR(src1_base + 0x01, lane_bv) @ rVGPR(src1_base, lane_bv)
            };

            let result : QWORD = get_slice_int(64, shl_int(unsigned(value), shift_amt), 0);
            wVGPR(vdst, lane_bv, result[31..0]);
            wVGPR(vdst + 0x01, lane_bv, result[63..32])
        }
    }
}

val v_add_co_u32 : (vgpr_idx, sgpr_idx, vop_src, vop_src) -> unit
function v_add_co_u32(vdst, carry_dst, src0, src1) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u < 256 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;
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
            let tmp : bits(33) = (0b0 @ op0) + (0b0 @ op1);
            results[lane] = tmp[31..0];
            carry[lane..lane] = tmp[32..32]
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, results[lane])
        }
    };

    wSGPR(carry_dst, carry)
}

// VOP3SD Instructions
val v_mad_u64_u32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_mad_u64_u32(vdst, sdst, src0, src1, src2) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);
    let src2_u = unsigned(src2);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u < 256 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };

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

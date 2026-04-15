// VOP2 Instructions

// NOP stub: we only need the parser to not crash; results are irrelevant.
val v_and_b32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_and_b32(vdst, src0, src1) = { () }

val v_ashrrev_i32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_ashrrev_i32(vdst, vsrc, src0) = {
    let src0_u = unsigned(src0);
    let vsrc_u = unsigned(vsrc);

    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if vsrc_u <= 255 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let shift_src : DWORD = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let value : DWORD = if vsrc_u <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, vsrc_u - 256, 0), lane_bv)
            };
            let shift_amt : int = unsigned(shift_src[4..0]);
            results[lane] = get_slice_int(32, shr_int(signed(value), shift_amt), 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_lshl_add_u32 : (vgpr_idx, sgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_lshl_add_u32(vdst, sdst, src0, src1, src2) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);
    let src2_u = unsigned(src2);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u < 256 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };
    let op2_common : DWORD = if src2_u < 256 then {
        read_vector_source(src2, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 : DWORD = if src0_u < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 : DWORD = if src1_u < 256 then { op1_common } else {
                rVGPR(get_slice_int(8, src1_u - 256, 0), lane_bv)
            };
            let op2 : DWORD = if src2_u < 256 then { op2_common } else {
                rVGPR(get_slice_int(8, src2_u - 256, 0), lane_bv)
            };
            let shift_amt : int = unsigned(op1[4..0]);
            let shifted : DWORD = get_slice_int(32, shl_int(unsigned(op0), shift_amt), 0);
            results[lane] = get_slice_int(32, unsigned(shifted) + unsigned(op2), 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_add3_u32 : (vgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_add3_u32(vdst, src0, src1, src2) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);
    let src2_u = unsigned(src2);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u < 256 then {
        read_vector_source(src1, 0b00000)
    } else { 0x00000000 };
    let op2_common : DWORD = if src2_u < 256 then {
        read_vector_source(src2, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 : DWORD = if src0_u < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 : DWORD = if src1_u < 256 then { op1_common } else {
                rVGPR(get_slice_int(8, src1_u - 256, 0), lane_bv)
            };
            let op2 : DWORD = if src2_u < 256 then { op2_common } else {
                rVGPR(get_slice_int(8, src2_u - 256, 0), lane_bv)
            };
            results[lane] = get_slice_int(32, unsigned(op0) + unsigned(op1) + unsigned(op2), 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_add_nc_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_add_nc_u32(vdst, vsrc, src0) = {
    let src0_u = unsigned(src0);
    let vsrc_u = unsigned(vsrc);

    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if vsrc_u <= 255 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 = if vsrc_u <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, vsrc_u - 256, 0), lane_bv)
            };
            let res = unsigned(op0) + unsigned(op1);
            results[lane] = get_slice_int(32, res, 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_add_co_ci_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_add_co_ci_u32(vdst, vsrc, src0) = {
    let src0_u = unsigned(src0);
    let vsrc_u = unsigned(vsrc);

    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if vsrc_u <= 255 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;
    let carry_in : bits(32) = rVCC()[31..0];
    var carry_out : bits(32) = 0x00000000;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let op1 = if vsrc_u <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, vsrc_u - 256, 0), lane_bv)
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
        wVGPR(vdst, lane_bv, results[lane])
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
        wVGPR(vdst, lane_bv, results[lane])
    };

    wSGPR(carry_dst, carry_out)
}

// VOP1 Instructions
val v_mov_b32 : (vgpr_idx, vop_src) -> unit
function v_mov_b32(vdst, src0) = {
    let src0_u = unsigned(src0);

    let val_common : DWORD = if src0_u <= 255 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            results[lane] =
                if src0_u <= 255 then { val_common } else {
                    rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
                }
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_lshlrev_b32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_lshlrev_b32(vdst, vsrc, src0) = {
    let src0_u = unsigned(src0);
    let vsrc_u = unsigned(vsrc);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if vsrc_u < 256 then {
        read_vector_source(vsrc, 0b00000)
    } else { 0x00000000 };

    var results : vector(32, dec, bits(32)) = undefined;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let shift_src : DWORD = if src0_u < 256 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let value : DWORD = if vsrc_u < 256 then { op1_common } else {
                rVGPR(get_slice_int(8, vsrc_u - 256, 0), lane_bv)
            };
            let shift_amt : int = unsigned(shift_src[4..0]);
            results[lane] = get_slice_int(32, shl_int(unsigned(value), shift_amt), 0)
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

// VOP3 Instructions
val v_lshlrev_b64 : (vgpr_idx, vop_src, vop_src) -> unit
function v_lshlrev_b64(vdst, src0, src1) = {
    let src0_u = unsigned(src0);
    let src1_u = unsigned(src1);

    let op0_common : DWORD = if src0_u < 256 then {
        read_vector_source(src0, 0b00000)
    } else { 0x00000000 };

    let op1_common : QWORD = if src1_u < 256 then {
        read_scalar_source64(get_slice_int(8, src1_u, 0))
    } else { 0x0000000000000000 };

    var results_lo : vector(32, dec, bits(32)) = undefined;
    var results_hi : vector(32, dec, bits(32)) = undefined;

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
            results_lo[lane] = result[31..0];
            results_hi[lane] = result[63..32]
        } else {
            results_lo[lane] = rVGPR(vdst, lane_bv);
            results_hi[lane] = rVGPR(vdst + 0x01, lane_bv)
        }
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results_lo[lane]);
        wVGPR(vdst + 0x01, lane_bv, results_hi[lane])
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
        wVGPR(vdst, lane_bv, results[lane])
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
        wVGPR(vdst, lane_bv, results_lo[lane]);
        wVGPR(vdst + 0x01, lane_bv, results_hi[lane])
    };

    wSGPR(sdst[6..0], carry)
}

val v_cmp_lt_u32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_cmp_lt_u32(vdst, vsrc0, vsrc1) = {
    var vcc_result : bits(32) = 0x00000000;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let val0 : DWORD = read_vector_source(vsrc0, lane_bv);
            let val1 : DWORD = read_vector_source(vsrc1, lane_bv);
            if unsigned(val0) < unsigned(val1) then {
                vcc_result[lane..lane] = 0b1
            }
        }
    };

    // Write result to SGPR pair at vdst (lower) and vdst+1 (upper, 0 for wave32).
    // When VOPC-encoded, vdst = 106 (VCC_LO); when VOP3-encoded, vdst is explicit.
    wSGPR(vdst[6..0], vcc_result);
    wSGPR(vdst[6..0] + 0b0000001, 0x00000000)
}

val v_cmp_gt_i32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_cmp_gt_i32(vdst, vsrc0, vsrc1) = {
    let src0_u = unsigned(vsrc0);
    let src1_u = unsigned(vsrc1);
    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(vsrc0, 0b00000)
    } else { 0x00000000 };
    let op1_common : DWORD = if src1_u <= 255 then {
        read_vector_source(vsrc1, 0b00000)
    } else { 0x00000000 };

    var result : bits(32) = 0x00000000;
    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let val0 : DWORD = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let val1 : DWORD = if src1_u <= 255 then { op1_common } else {
                rVGPR(get_slice_int(8, src1_u - 256, 0), lane_bv)
            };
            if signed(val0) > signed(val1) then {
                result[lane..lane] = 0b1
            }
        }
    };
    wSGPR(vdst[6..0], result);
    wSGPR(vdst[6..0] + 0b0000001, 0x00000000)
}

val v_cndmask_b32 : (vgpr_idx, vop_src, vop_src) -> unit
function v_cndmask_b32(vdst, vsrc0, vsrc1) = {
    let src0_u = unsigned(vsrc0);
    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(vsrc0, 0b00000)
    } else { 0x00000000 };
    let mask : bits(32) = rVCC()[31..0];

    var results : vector(32, dec, bits(32)) = undefined;
    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let src0 : DWORD = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let src1 : DWORD = read_vector_source(vsrc1, lane_bv);
            results[lane] = if mask[lane..lane] == 0b1 then src1 else src0
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };
    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

val v_cndmask_b32_vop3 : (vgpr_idx, vop_src, vop_src, vop_src) -> unit
function v_cndmask_b32_vop3(vdst, vsrc0, vsrc1, vsrc2) = {
    let src0_u = unsigned(vsrc0);
    let op0_common : DWORD = if src0_u <= 255 then {
        read_vector_source(vsrc0, 0b00000)
    } else { 0x00000000 };
    let mask : bits(32) = read_common_source(unsigned(vsrc2));

    var results : vector(32, dec, bits(32)) = undefined;
    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let src0 : DWORD = if src0_u <= 255 then { op0_common } else {
                rVGPR(get_slice_int(8, src0_u - 256, 0), lane_bv)
            };
            let src1 : DWORD = read_vector_source(vsrc1, lane_bv);
            results[lane] = if mask[lane..lane] == 0b1 then src1 else src0
        } else {
            results[lane] = rVGPR(vdst, lane_bv)
        }
    };
    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        wVGPR(vdst, lane_bv, results[lane])
    }
}

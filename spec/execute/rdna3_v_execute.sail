// VOP2 Instructions

val v_add_nc_u32 : (vector_dst, vop_src, vop_src) -> unit
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

val v_mov_b32 : (vector_dst, vop_src) -> unit
function v_mov_b32(vdst, src0) = {
    let val_to_move = read_vector_source(src0, 0b00000);

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, val_to_move)
        }
    }
}

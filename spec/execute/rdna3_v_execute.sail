// VOP2 Instructions

val v_add_nc_u32 : (vector_dst, vector_src, vop_src) -> unit
function v_add_nc_u32(vdst, src1, src0) = {
    let op0_base = if unsigned(src0) == 255 then {
        fetch_inst(PC + 4)
    } else {
        read_common_source(unsigned(src0))
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let op0 = if unsigned(src0) <= 255 then { op0_base } else {
                rVGPR(get_slice_int(8, unsigned(src0) - 256, 0), lane_bv)
            };

            let op1 = rVGPR(src1, lane_bv);

            let result_int = unsigned(op0) + unsigned(op1);
            let result_bits = get_slice_int(32, result_int, 0);

            wVGPR(vdst, lane_bv, result_bits)
        }
    }
}

val v_mov_b32 : (vector_dst, vop_src) -> unit
function v_mov_b32(vdst, src0) = {
    var val_to_move : DWORD = 0x00000000;
    if unsigned(src0) == 255 then {
        val_to_move = fetch_inst(PC + 4);
        print_bits("[GPU] V_MOV: Loading Literal 0x", val_to_move)
    } else {
        val_to_move = read_common_source(unsigned(src0))
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            wVGPR(vdst, lane_bv, val_to_move)
        }
    }
}

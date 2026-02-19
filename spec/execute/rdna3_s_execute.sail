// SOP2 Instructions

val s_add_u32 : (scalar_dst, scalar_src, scalar_src) -> unit
function s_add_u32(sdst, ssrc0, ssrc1) = {
    let val0 = read_scalar_source(ssrc0);
    let val1 = read_scalar_source(ssrc1);
    let result : int  = unsigned(val0) + unsigned(val1);

    let result_bits : bits(32) = get_slice_int(32, result, 0);
    let carry : bit = if result > MAX_UINT32 then bitone else bitzero;
    wSGPR(sdst, result_bits);
    wSCC(carry);
}


val s_sub_u32 : (scalar_dst, scalar_src, scalar_src) -> unit
function s_sub_u32(sdst, ssrc0, ssrc1) = {
    let val0 = read_scalar_source(ssrc0);
    let val1 = read_scalar_source(ssrc1);
    let result : int  = unsigned(val0) - unsigned(val1);

    let result_bits : bits(32) = get_slice_int(32, result, 0);
    let carry : bit = if result >= 0 then bitone else bitzero;
    wSGPR(sdst, result_bits);
    wSCC(carry);
}

// SOP1 Instructions

val s_mov_b32 : (scalar_dst, scalar_src) -> unit
function s_mov_b32(sdst, ssrc0) = {
    wSGPR(sdst, read_scalar_source(ssrc0))
    // doesn't affect SCC
}

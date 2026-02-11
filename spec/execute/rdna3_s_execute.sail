val do_s_add_u32 : (scalar_dst, scalar_src, scalar_src) -> unit
function do_s_add_u32(sdst, ssrc0, ssrc1) = {
    let val0 = rSGPR(ssrc0);
    let val1 = rSGPR(ssrc1);
    let result = val0 + val1;

    wSGPR(dst_id, result);
    //wSCC();
}
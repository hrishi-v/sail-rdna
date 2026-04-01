// SOP2 Instructions

val s_add_u32 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_add_u32(sdst, ssrc0, ssrc1) = {
    let val0 = read_common_source(unsigned(ssrc0));
    let val1 = read_common_source(unsigned(ssrc1));
    let result : int = unsigned(val0) + unsigned(val1);

    let result_bits : bits(32) = get_slice_int(32, result, 0);
    let carry : bit = if result > MAX_UINT32 then { bitone } else { bitzero };
    wSGPR(sdst, result_bits);
    wSCC(carry)
}

val s_sub_u32 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_sub_u32(sdst, ssrc0, ssrc1) = {
    let val0 = read_common_source(unsigned(ssrc0));
    let val1 = read_common_source(unsigned(ssrc1));
    let result : int = unsigned(val0) - unsigned(val1);

    let result_bits : bits(32) = get_slice_int(32, result, 0);
    let carry : bit = if result >= 0 then { bitone } else { bitzero };
    wSGPR(sdst, result_bits);
    wSCC(carry)
}

val s_lshr_b64 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_lshr_b64(sdst, ssrc0, ssrc1) = {
    let val0 : QWORD = read_scalar_source64(ssrc0);
    let val1 : DWORD = read_common_source(unsigned(ssrc1));

    let shift_amt : int = unsigned(val1[5..0]);
    let val0_int : int = unsigned(val0);

    let shifted_int : int = shr_int(val0_int, shift_amt);
    let result : QWORD = get_slice_int(64, shifted_int, 0);

    let scc_val : bit = if result != 0x0000000000000000 then { bitone } else { bitzero };

    write_scalar_dst64(sdst, result);
    wSCC(scc_val)
}

val s_cselect_b32 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_cselect_b32(sdst, ssrc0, ssrc1) = {
    let value = if rSCC() == bitone then {
        read_common_source(unsigned(ssrc0))
    } else {
        read_common_source(unsigned(ssrc1))
    };
    wSGPR(sdst, value)
}

// SOP1 Instructions
val s_mov_b32 : (sgpr_idx, sgpr_src) -> unit
function s_mov_b32(sdst, ssrc0) = {
    wSGPR(sdst, read_common_source(unsigned(ssrc0)))
    // doesn't affect SCC
}

val s_mov_b64 : (sgpr_idx, sgpr_src) -> unit
function s_mov_b64(sdst, ssrc0) = {
    write_scalar_dst64(sdst, read_scalar_source64(ssrc0))
}

// SOPC Instructions
val s_cmp_eq_i32 : (sgpr_src, sgpr_src) -> unit
function s_cmp_eq_i32(ssrc0, ssrc1) = {
    let val0 = read_common_source(unsigned(ssrc0));
    let val1 = read_common_source(unsigned(ssrc1));

    if val0 == val1 then {
        wSCC(bitone)
    } else {
        wSCC(bitzero)
    }
}

val s_cmp_lg_i32 : (sgpr_src, sgpr_src) -> unit
function s_cmp_lg_i32(ssrc0, ssrc1) = {
    let val0 = read_common_source(unsigned(ssrc0));
    let val1 = read_common_source(unsigned(ssrc1));

    if val0 != val1 then {
        wSCC(bitone)
    } else {
        wSCC(bitzero)
    }
}

// SOPP Instructions
val s_clause : unit -> unit
function s_clause () = {
    // TODO: Hardware only instruction? Check this!
    ()
}

val s_delay_alu : unit -> unit
function s_delay_alu () = {
    // TODO: Hardware only instruction? Check this!
    ()
}

val s_endpgm : unit -> unit
function s_endpgm () = {
    // TODO: Hardware implicitly executes S_WAITCNT 0 and S_WAITCNT_VSCNT 0 here.
    // Currently omitted.
    // Is this where the predicted cycle count is output?
    print(">>> S_ENDPGM REACHED: Halting Wavefront <<<\n");
    set_halt_flag()
}

val s_branch : bits(16) -> unit
function s_branch simm = {
    let offset : QWORD = get_slice_int(64, signed(simm) * 4, 0); // multiplied to convert from DWORDS (32-bit) to bytes!
    PC = PC + offset
}

val s_waitcnt : bits(16) -> unit
function s_waitcnt simm = {
    // Should likely include a cycle count incrementer for my estimate!
    ()
}

// SMEM Instructions
val s_load_b64 : (bits(6), sgpr_idx, bits(21), sgpr_idx) -> unit
function s_load_b64(sbase, sdata, offset, soffset) = {
    let base_idx = unsigned(sbase) * 2;
    let base_lo : sgpr_src = get_slice_int(8, base_idx, 0);
    let base_hi : sgpr_src = get_slice_int(8, base_idx + 1, 0);

    let addr_lo = read_common_source(unsigned(base_lo));
    let addr_hi = read_common_source(unsigned(base_hi));
    let base_addr : QWORD = EXTZ(addr_hi) @ addr_lo;

    let imm_offset : QWORD = EXTS(offset);

    let soff : QWORD = if unsigned(soffset) == 127 then { 0x0000000000000000 } else {
        EXTZ(read_common_source(unsigned(soffset)))
    };

    let final_addr = base_addr + imm_offset + soff;

    let data_lo = read_mem_32(final_addr);
    let data_hi = read_mem_32(final_addr + 4);
    let dst : sgpr_idx = get_slice_int(7, unsigned(sdata), 0);
    write_scalar_dst64(dst, EXTZ(data_hi) @ data_lo)
}

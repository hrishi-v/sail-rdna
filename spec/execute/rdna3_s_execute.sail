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

val s_and_b32 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_and_b32(sdst, ssrc0, ssrc1) = {
    let val0 : DWORD = read_common_source(unsigned(ssrc0));
    let val1 : DWORD = read_common_source(unsigned(ssrc1));
    let result : DWORD = val0 & val1;
    wSGPR(sdst, result);
    wSCC(if result == 0x00000000 then bitzero else bitone)
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

val s_and_not1_b32 : (sgpr_idx, sgpr_src, sgpr_src) -> unit
function s_and_not1_b32(sdst, ssrc0, ssrc1) = {
    let src0 : DWORD = read_common_source(unsigned(ssrc0));
    let src1 : DWORD = read_common_source(unsigned(ssrc1));

    let result : DWORD = src0 & not_vec(src1);
    wSGPR(sdst, result);
    wSCC(if unsigned(result) == 0 then bitzero else bitone)
}

// SOP1 Instructions
val s_mov_b32 : (sgpr_idx, sgpr_src) -> unit
function s_mov_b32(sdst, ssrc0) = {
    wSGPR(sdst, read_common_source(unsigned(ssrc0)))
}

val s_mov_b64 : (sgpr_idx, sgpr_src) -> unit
function s_mov_b64(sdst, ssrc0) = {
    write_scalar_dst64(sdst, read_scalar_source64(ssrc0))
}

val s_and_saveexec_b32 : (sgpr_idx, sgpr_src) -> unit
function s_and_saveexec_b32(sdst, ssrc0) = {
    let save_exec : DWORD = EXEC_LO;
    let new_exec : DWORD = read_common_source(unsigned(ssrc0)) & save_exec;

    wSGPR(sdst, save_exec);
    EXEC_LO = new_exec;
    wSCC(if new_exec == 0x00000000 then bitzero else bitone)
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

val s_bitcmp0_b32 : (sgpr_src, sgpr_src) -> unit
function s_bitcmp0_b32(ssrc0, ssrc1) = {
    let val0 : DWORD = read_common_source(unsigned(ssrc0));
    let val1 : DWORD = read_common_source(unsigned(ssrc1));
    let bit_idx : int = unsigned(val1[4..0]);
    let sel : DWORD = get_slice_int(32, shl_int(1, bit_idx), 0);
    if (val0 & sel) == 0x00000000 then {
        wSCC(bitone)
    } else {
        wSCC(bitzero)
    }
}

// SOPP Instructions
val s_nop : unit -> unit
function s_nop () = { () }

val s_cbranch_scc1 : simm_16 -> unit
function s_cbranch_scc1 simm = {
    // NOP stub: branch semantics not needed for hazard detection.
    ()
}

val s_sendmsg : simm_16 -> unit
function s_sendmsg simm = {
    if simm[3..0] == 0b0011 then {
        var queue_nonempty : bool = unsigned(VMCNT) > 0;
        foreach (i from 0 to 255) {
            if VMQ_PENDING[i] == 0b1 then {
                queue_nonempty = true
            }
        };
        if queue_nonempty then {
            print("[HAZARD] Fatal Semantic Hazard: MSG_DEALLOC_VGPRS issued while VMEM queue is not empty.\n");
            halt_flag = 0b1;
            error_flag = 0b1
        }
    }
}

val s_clause : unit -> unit
function s_clause () = { () }

val s_delay_alu : unit -> unit
function s_delay_alu () = { () }

val s_endpgm : unit -> unit
function s_endpgm () = {
    if unsigned(VSCNT) > 0 then {
        print("[HAZARD] s_endpgm with outstanding vector stores (vscnt=");
        print_int("", unsigned(VSCNT));
        print(") — missing s_waitcnt_vscnt\n")
    };
    print(">>> S_ENDPGM REACHED: Halting Wavefront <<<\n");
    set_halt_flag()
}

val s_branch : simm_16 -> unit
function s_branch simm = {
    let offset : QWORD = get_slice_int(64, signed(simm) * 4, 0); 
    PC = PC + offset
}

val s_waitcnt : simm_16 -> unit
function s_waitcnt simm = {
    let vmcnt_target : bits(6) = simm[15..10];
    if vmcnt_target != 0b111111 then {
        let target_ext : bits(7) = 0b0 @ vmcnt_target;
        if unsigned(VMCNT) > unsigned(target_ext) then {
            let to_drain : int = unsigned(VMCNT) - unsigned(target_ext);
            foreach (iteration from 0 to 127) {
                if iteration < to_drain then {
                    vlq_pop_oldest()
                }
            };
            VMCNT = target_ext;
            vmq_rebuild_pending()
        }
    };
    let lgkm_target : bits(6) = simm[9..4];
    if lgkm_target != 0b111111 then {
        foreach (iteration from 0 to 15) {
            if unsigned(LGKMCNT) > unsigned(lgkm_target) then {
                if unsigned(PLQ_COUNT) > 0 then {
                    let dst_base : int = unsigned(PLQ_DST[0]);
                    let ndw : int = unsigned(PLQ_NDW[0]);
                    foreach (k from 0 to 7) {
                        if k < ndw then {
                            let dst_k : sgpr_idx = get_slice_int(7, dst_base + k, 0);
                            wSGPR(dst_k, PLQ_VAL[0][k])
                        }
                    };
                    foreach (j from 0 to 14) {
                        if j < unsigned(PLQ_COUNT) - 1 then {
                            PLQ_DST[j] = PLQ_DST[j + 1];
                            PLQ_NDW[j] = PLQ_NDW[j + 1];
                            PLQ_VAL[j] = PLQ_VAL[j + 1]
                        }
                    };
                    PLQ_COUNT = PLQ_COUNT + 0b11111;
                    LGKMCNT = LGKMCNT + 0b111111
                } else {
                    if unsigned(DS_PENDING) > 0 then {
                        DS_PENDING = DS_PENDING + 0b11111;
                        LGKMCNT = LGKMCNT + 0b111111
                    }
                }
            }
        }
    }
}

// SOPK Instructions
val s_waitcnt_vscnt : simm_16 -> unit
function s_waitcnt_vscnt simm = {
    let target : bits(6) = simm[5..0];
    foreach (i from 0 to 62) {
        if unsigned(VSCNT) > unsigned(target) then {
            VSCNT = VSCNT + 0b111111;
            vsq_pop_oldest()
        }
    }
}

// SMEM Instructions
val smem_final_addr : (sbase, offset_21, sgpr_idx) -> QWORD
function smem_final_addr(sbase, offset, soffset) = {
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

    base_addr + imm_offset + soff
}

val s_load_b32 : (sbase, sgpr_idx, offset_21, sgpr_idx) -> unit
function s_load_b32(sbase, sdata, offset, soffset) = {
    let final_addr = smem_final_addr(sbase, offset, soffset);
    let data = read_mem_32(final_addr);
    let dst : sgpr_idx = get_slice_int(7, unsigned(sdata), 0);
    let idx = unsigned(PLQ_COUNT);
    if idx < 16 then {
        PLQ_DST[idx] = dst;
        PLQ_NDW[idx] = 0b0001;
        PLQ_VAL[idx][0] = data;
        PLQ_COUNT = PLQ_COUNT + 1;
        LGKMCNT = LGKMCNT + 1
    }
}

val s_load_b64 : (sbase, sgpr_idx, offset_21, sgpr_idx) -> unit
function s_load_b64(sbase, sdata, offset, soffset) = {
    let final_addr = smem_final_addr(sbase, offset, soffset);
    let dst : sgpr_idx = get_slice_int(7, unsigned(sdata), 0);
    let idx = unsigned(PLQ_COUNT);
    if idx < 16 then {
        PLQ_DST[idx] = dst;
        PLQ_NDW[idx] = 0b0010;
        PLQ_VAL[idx][0] = read_mem_32(final_addr);
        PLQ_VAL[idx][1] = read_mem_32(final_addr + 4);
        PLQ_COUNT = PLQ_COUNT + 1;
        LGKMCNT = LGKMCNT + 1
    }
}

val s_load_b128 : (sbase, sgpr_idx, offset_21, sgpr_idx) -> unit
function s_load_b128(sbase, sdata, offset, soffset) = {
    let final_addr = smem_final_addr(sbase, offset, soffset);
    let dst : sgpr_idx = get_slice_int(7, unsigned(sdata), 0);
    let idx = unsigned(PLQ_COUNT);
    if idx < 16 then {
        PLQ_DST[idx] = dst;
        PLQ_NDW[idx] = 0b0100;
        foreach (k from 0 to 3) {
            let off : QWORD = get_slice_int(64, k * 4, 0);
            PLQ_VAL[idx][k] = read_mem_32(final_addr + off)
        };
        PLQ_COUNT = PLQ_COUNT + 1;
        LGKMCNT = LGKMCNT + 1
    }
}

val s_load_b256 : (sbase, sgpr_idx, offset_21, sgpr_idx) -> unit
function s_load_b256(sbase, sdata, offset, soffset) = {
    let final_addr = smem_final_addr(sbase, offset, soffset);
    let dst : sgpr_idx = get_slice_int(7, unsigned(sdata), 0);
    let idx = unsigned(PLQ_COUNT);
    if idx < 16 then {
        PLQ_DST[idx] = dst;
        PLQ_NDW[idx] = 0b1000;
        foreach (k from 0 to 7) {
            let off : QWORD = get_slice_int(64, k * 4, 0);
            PLQ_VAL[idx][k] = read_mem_32(final_addr + off)
        };
        PLQ_COUNT = PLQ_COUNT + 1;
        LGKMCNT = LGKMCNT + 1
    }
}
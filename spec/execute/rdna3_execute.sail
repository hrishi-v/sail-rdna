val execute : ast -> unit
function execute inst = {
    match inst {
        // SOP2
        Inst_S_ADD_U32(d, s0, s1) => s_add_u32(d, s0, s1),
        Inst_S_SUB_U32(d, s0, s1) => s_sub_u32(d, s0, s1),
        Inst_S_CSELECT_B32(d, s0, s1) => s_cselect_b32(d, s0, s1),
        Inst_S_LSHR_B64(d, s0, s1) => s_lshr_b64(d, s0, s1),
        // SOP1
        Inst_S_MOV_B32(d, s0) => s_mov_b32(d, s0),
        Inst_S_MOV_B64(d, s0) => s_mov_b64(d, s0),
        // SOPC
        Inst_S_CMP_EQ_I32(s0, s1) => s_cmp_eq_i32(s0, s1),
        Inst_S_CMP_LG_I32(s0, s1) => s_cmp_lg_i32(s0, s1),
        // SOPP
        Inst_S_CLAUSE() => s_clause(),
        Inst_S_DELAY_ALU() => s_delay_alu(),
        Inst_S_WAITCNT(simm) => s_waitcnt(simm),
        Inst_S_BRANCH(simm) => s_branch(simm),
        Inst_S_ENDPGM() => s_endpgm(),
        // VOP3
        Inst_V_LSHLREV_B64(vd, s0, s1) => v_lshlrev_b64(vd, s0, s1),
        Inst_V_MAD_U64_U32(vd, sd, s0, s1, s2) => v_mad_u64_u32(vd, sd, s0, s1, s2),
        // VOP2
        Inst_V_ASHRREV_I32(vd, vs, s) => v_ashrrev_i32(vd, vs, s),
        Inst_V_ADD_NC_U32(vd, vs, s) => v_add_nc_u32(vd, vs, s),
        // SMEM
        Inst_S_LOAD_B64(sbase, sdata, offset, soffset) => s_load_b64(sbase, sdata, offset, soffset),
        // VOP1
        Inst_V_MOV_B32(vd, s) => v_mov_b32(vd, s),
        // FLAT
        Inst_FLAT_LOAD_B32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) => flat_load_b32(
            offset,
            dlc,
            glc,
            slc,
            seg,
            op,
            addr,
            data,
            saddr,
            sve,
            vdst,
        ),
        Inst_FLAT_STORE_B32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) => flat_store_b32(
            offset,
            dlc,
            glc,
            slc,
            seg,
            op,
            addr,
            data,
            saddr,
            sve,
            vdst,
        ),
        Inst_FLAT_LOAD_B64(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) => flat_load_b64(
            offset,
            dlc,
            glc,
            slc,
            seg,
            op,
            addr,
            data,
            saddr,
            sve,
            vdst,
        ),
        Inst_FLAT_STORE_B64(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) => flat_store_b64(
            offset,
            dlc,
            glc,
            slc,
            seg,
            op,
            addr,
            data,
            saddr,
            sve,
            vdst,
        ),
        // General
        Inst_INVALID() => {
            print("Error: Executing invalid instruction\n");
            halt_flag = 0b1;
            error_flag = 0b1
        },
        _ => print("Error: Unimplemented instruction execution"),
    }
}

val flat_load_b32 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function flat_load_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base = SHARED_BASE;
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);

        if EXEC_LO[lane..lane] == 0b1 then {
            let addr_lo = rVGPR(addr, lane_bv);
            let addr_hi = rVGPR(addr + 0x01, lane_bv);
            let v_addr : QWORD = addr_hi @ addr_lo;
            let final_addr = v_addr + actual_offset;

            let is_shared = unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(
                shared_limit[31..0],
            );
            if is_shared then {
                let read_data = read_mem_32(final_addr);
                wVGPR(vdst, lane_bv, read_data);
                LGKMCNT = LGKMCNT + 1
            } else {
                let read_data = read_mem_32(final_addr);
                wVGPR(vdst, lane_bv, read_data);
                VMCNT = VMCNT + 1
            }
        }
    }
}

val flat_store_b32 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function flat_store_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base = SHARED_BASE;
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);

        if EXEC_LO[lane..lane] == 0b1 then {
            let addr_lo = rVGPR(addr, lane_bv);
            let addr_hi = rVGPR(addr + 0x01, lane_bv);
            let v_addr : QWORD = addr_hi @ addr_lo;

            let final_addr = v_addr + actual_offset;
            let write_data = rVGPR(data, lane_bv);
            let is_shared = unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(
                shared_limit[31..0],
            );

            if is_shared then {
                write_mem_32(final_addr, write_data);
                LGKMCNT = LGKMCNT + 0b000001
            } else {
                write_mem_32(final_addr, write_data);

                VMCNT = VMCNT + 0b000001
            }
        }
    }
}

val flat_load_b64 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function flat_load_b64(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base = SHARED_BASE;
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);

        if EXEC_LO[lane..lane] == 0b1 then {
            let addr_lo = rVGPR(addr, lane_bv);
            let addr_hi = rVGPR(addr + 0x01, lane_bv);
            let v_addr : QWORD = addr_hi @ addr_lo;
            let final_addr = v_addr + actual_offset;

            let is_shared = unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(
                shared_limit[31..0],
            );
            if is_shared then {
                let read_data : QWORD = read_mem_64(final_addr);
                let read_data_lo : DWORD = read_data[31..0];
                let read_data_hi : DWORD = read_data[63..32];
                wVGPR(vdst, lane_bv, read_data_lo);
                wVGPR(vdst + 0x01, lane_bv, read_data_hi);
                LGKMCNT = LGKMCNT + 1
            } else {
                let read_data : QWORD = read_mem_64(final_addr);
                let read_data_lo : DWORD = read_data[31..0];
                let read_data_hi : DWORD = read_data[63..32];
                wVGPR(vdst, lane_bv, read_data_lo);
                wVGPR(vdst + 0x01, lane_bv, read_data_hi);
                VMCNT = VMCNT + 1
            }
        }
    }
}

val flat_store_b64 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function flat_store_b64(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base = SHARED_BASE;
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);

        if EXEC_LO[lane..lane] == 0b1 then {
            let addr_lo : DWORD = rVGPR(addr, lane_bv);
            let addr_hi : DWORD = rVGPR(addr + 0x01, lane_bv);
            let v_addr : QWORD = addr_hi @ addr_lo;

            let final_addr : QWORD = v_addr + actual_offset;
            let write_data_lo : DWORD = rVGPR(data, lane_bv);
            let write_data_hi : DWORD = rVGPR(data + 0x01, lane_bv);
            let write_data : QWORD = write_data_hi @ write_data_lo;
            let is_shared = unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(
                shared_limit[31..0],
            );

            if is_shared then {
                write_mem_64(final_addr, write_data);
                LGKMCNT = LGKMCNT + 1
            } else {
                write_mem_64(final_addr, write_data);

                VMCNT = VMCNT + 1
            }
        }
    }
}

val global_load_b32 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function global_load_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let saddr_u = unsigned(saddr);

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let final_addr : QWORD = if saddr_u == unsigned(0x7F) then {
                // saddr=null: VGPR pair is the full 64-bit address
                let addr_lo = rVGPR(addr, lane_bv);
                let addr_hi = rVGPR(addr + 0x01, lane_bv);
                (addr_hi @ addr_lo) + EXTZ(offset)
            } else {
                // SGPR pair is the 64-bit base; VGPR is a 32-bit per-lane offset
                let base_lo : DWORD = rSGPR(saddr);
                let base_hi : DWORD = rSGPR(get_slice_int(7, saddr_u + 1, 0));
                let base : QWORD = base_hi @ base_lo;
                base + EXTZ(rVGPR(addr, lane_bv)) + EXTZ(offset)
            };
            let read_data = read_mem_32(final_addr);
            wVGPR(vdst, lane_bv, read_data);
            VMCNT = VMCNT + 1
        }
    }
}

val global_store_b32 : (
        bits(12),
        bits(1),
        bits(1),
        bits(1),
        bits(2),
        BYTE,
        vgpr_idx,
        vgpr_idx,
        sgpr_idx,
        bits(1),
        vgpr_idx,
    ) -> unit
function global_store_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let saddr_u = unsigned(saddr);

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let final_addr : QWORD = if saddr_u == unsigned(0x7F) then {
                // saddr=null: VGPR pair is the full 64-bit address
                let addr_lo = rVGPR(addr, lane_bv);
                let addr_hi = rVGPR(addr + 0x01, lane_bv);
                (addr_hi @ addr_lo) + EXTZ(offset)
            } else {
                // SGPR pair is the 64-bit base; VGPR is a 32-bit per-lane offset
                let base_lo : DWORD = rSGPR(saddr);
                let base_hi : DWORD = rSGPR(get_slice_int(7, saddr_u + 1, 0));
                let base : QWORD = base_hi @ base_lo;
                base + EXTZ(rVGPR(addr, lane_bv)) + EXTZ(offset)
            };
            let write_data = rVGPR(data, lane_bv);
            write_mem_32(final_addr, write_data);
            VMCNT = VMCNT + 1
        }
    }
}

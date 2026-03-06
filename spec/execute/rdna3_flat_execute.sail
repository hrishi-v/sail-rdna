val flat_load_b32 : (flat_offset, flat_dlc_bit, flat_glc_bit, flat_slc_bit, flat_seg, flat_op, flat_addr, flat_data, flat_saddr, flat_sve_bit, flat_vdst) -> unit
function flat_load_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base  = SHARED_BASE; 
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31 by 1) {
        let lane_bv = get_slice_int(5, lane, 0);
        
        if (EXEC_LO[lane..lane] == 0b1) then {
            let addr_lo = rVGPR(addr, lane_bv);
            let addr_hi = rVGPR(addr + 0x01, lane_bv); 
            let v_addr : QWORD = addr_hi @ addr_lo;
            let final_addr = v_addr + actual_offset;
            
            let is_shared = (unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(shared_limit[31..0]));
            if is_shared then {
                let read_data = read_mem_32(final_addr); 
                wVGPR(vdst, lane_bv, read_data);
                LGKMCNT = LGKMCNT + 1; 
            } else {
                let read_data = read_mem_32(final_addr);
                wVGPR(vdst, lane_bv, read_data);
                VMCNT = VMCNT + 1; 
            }
        }
    }
}



val flat_store_b32 : (flat_offset, flat_dlc_bit, flat_glc_bit, flat_slc_bit, flat_seg, flat_op, flat_addr, flat_data, flat_saddr, flat_sve_bit, flat_vdst) -> unit
function flat_store_b32(offset, dlc, glc, slc, seg, op, addr, data, saddr, sve, vdst) = {
    let actual_offset : QWORD = EXTZ(offset[11..0]);
    let shared_base  = SHARED_BASE; 
    let shared_limit = SHARED_LIMIT;

    foreach (lane from 0 to 31 by 1) {
        let lane_bv = get_slice_int(5, lane, 0);
        
        if (EXEC_LO[lane..lane] == 0b1) then {
            let addr_lo = rVGPR(addr, lane_bv);
            let addr_hi = rVGPR(addr + 0x01, lane_bv); 
            let v_addr : QWORD = addr_hi @ addr_lo;
            
            let final_addr = v_addr + actual_offset;
            let write_data = rVGPR(data, lane_bv);
            let is_shared = (unsigned(final_addr[31..0]) >= unsigned(shared_base[31..0]) & unsigned(final_addr[31..0]) <= unsigned(shared_limit[31..0]));
            
            if is_shared then {
                write_mem_32(final_addr, write_data); 
                LGKMCNT = LGKMCNT + 0b000001; 
            } else {
                write_mem_32(final_addr, write_data);
                
                VMCNT = VMCNT + 0b000001; 
            }
        }
    }
}
val buffer_load_b128 : (
        vgpr_idx, vgpr_idx, srsrc_5, soffset_8, mem_offset_12, 
        flag_1, flag_1, flag_1, flag_1, flag_1
    ) -> unit
function buffer_load_b128(vdata, vaddr, srsrc, soffset, offset, offen, idxen, glc, slc, dlc) = {
    let rsrc_base_sgpr = unsigned(srsrc) * 4;
    let rsrc_word0 : DWORD = rSGPR(get_slice_int(7, rsrc_base_sgpr, 0));
    let rsrc_word1 : DWORD = rSGPR(get_slice_int(7, rsrc_base_sgpr + 1, 0));
    let base_addr : QWORD = EXTZ(rsrc_word1[15..0]) @ rsrc_word0;

    let soff_val : QWORD = if unsigned(soffset) == 128 then { 0x0000000000000000 } else {
        EXTZ(read_common_source(unsigned(soffset)))
    };

    foreach (lane from 0 to 31) {
        let lane_bv = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let voff_val : QWORD = if offen == 0b1 then {
                EXTZ(rVGPR(vaddr, lane_bv))
            } else { 0x0000000000000000 };

            // We ignore idxen here and assume stride=0 or flat addressing for simplicity
            // Full MUBUF involves stride and other fields, but we approximate for test needs
            let final_addr : QWORD = base_addr + voff_val + soff_val + EXTZ(offset);

            let data0 = read_mem_32(final_addr);
            let data1 = read_mem_32(final_addr + 4);
            let data2 = read_mem_32(final_addr + 8);
            let data3 = read_mem_32(final_addr + 12);

            wVGPR(vdata, lane_bv, data0);
            wVGPR(vdata + 0x01, lane_bv, data1);
            wVGPR(vdata + 0x02, lane_bv, data2);
            wVGPR(vdata + 0x03, lane_bv, data3)
        }
    };
    // A 128-bit load on GFX11 consumes 4 VMCNT credits!
    vmem_issue_load(vdata);
    vmem_issue_load(vdata + 0x01);
    vmem_issue_load(vdata + 0x02);
    vmem_issue_load(vdata + 0x03)
}
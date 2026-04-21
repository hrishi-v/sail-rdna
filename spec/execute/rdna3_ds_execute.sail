// LDS (Local Data Share) execution — ds_read_b32.
//
// LDS sandbox: the unified MEM array is 64 KB indexed by addr[15..0].
// LDS_BASE (default 0x8000) sandboxes LDS in the upper 32 KB, well clear
// of code and SMEM data that live near address 0.
//
// Effective per-lane address:
//   eff_addr = LDS_BASE + M0 + VGPR[vaddr][lane] + zero_extend(offset0)
//
// Bank conflict math (32 banks, each 4 bytes wide):
//   bank(lane) = (eff_byte_addr / 4) % 32

let LDS_BASE_LATENCY_CYCLES : int = 62

val lds_penalty_cycles : int -> int
function lds_penalty_cycles ways = {
    if ways <= 1 then { 0 } else {
        ways - 1
    }
}

val ds_read_b32 : (vgpr_idx, vgpr_idx, bits(8)) -> unit
function ds_read_b32(vdst, vaddr, offset) = {
    var max_hits : int = 0;
    var worst_bank : int = 0;
    var cnt : int = 0;
    foreach (b from 0 to 31) {
        cnt = 0;
        foreach (lane from 0 to 31) {
            let lane_bv : lane_id = get_slice_int(5, lane, 0);
            if EXEC_LO[lane..lane] == 0b1 then {
                // byte address within LDS (pre-sandbox offset, for bank math)
                let lane_addr : DWORD = rVGPR(vaddr, lane_bv) + EXTZ(offset);
                let bank : int = fmod_int(tdiv_int(unsigned(lane_addr), 4), 32);
                if bank == b then {
                    cnt = cnt + 1
                }
            }
        };
        if cnt > max_hits then {
            max_hits = cnt;
            worst_bank = b
        }
    };
    if max_hits > 1 then {
        print("[HAZARD] ds_read_b32: ");
        print_int("", max_hits);
        print("-way bank conflict on bank ");
        print_int("", worst_bank);
        print(". Expected replay penalty: ~");
        print_int("", lds_penalty_cycles(max_hits));
        print(" extra cycles (calibrate with tests/experiments/ds_read_b32_latency.py)\n")
    };

    let lds_base : QWORD = EXTZ(LDS_BASE);
    foreach (lane from 0 to 31) {
        let lane_bv : lane_id = get_slice_int(5, lane, 0);
        if EXEC_LO[lane..lane] == 0b1 then {
            let lane_addr : DWORD = rVGPR(vaddr, lane_bv) + EXTZ(offset);
            let eff_addr : QWORD = lds_base + EXTZ(M0) + EXTZ(lane_addr);
            let data = read_mem_32(eff_addr);
            wVGPR(vdst, lane_bv, data)
        }
    };

    LGKMCNT = LGKMCNT + 1;
    DS_PENDING = DS_PENDING + 1
}

// DS (Local Data Share) instruction decoder.
// Encoding bits[31:26] = 0b110110.
// Format (64-bit):
//   [7:0]   OFFSET0 — 8-bit byte offset added to the VGPR address
//   [15:8]  OFFSET1 — used only by read2/write2 variants; 0 here
//   [17]    GDS     — 0 = LDS, 1 = GDS; we only decode LDS (GDS=0)
//   [25:18] OP      — opcode
//   [39:32] ADDR    — VGPR index holding the per-lane byte address
//   [47:40] DATA0   — VGPR index for write source (unused for reads)
//   [55:48] DATA1   — second write source (unused here)
//   [63:56] VDST    — VGPR destination for read results

val ds_decode : QWORD -> ast
function ds_decode instr = {
    let offset0 : bits(8) = instr[7..0];
    let gds : bits(1) = instr[17..17];
    let opc : bits(8) = instr[25..18];
    let vaddr : vgpr_idx = instr[39..32];
    let vdst : vgpr_idx = instr[63..56];

    match (gds, opc) {
        // DS_READ_B32: OP = 54 = 0x36 = 0b00110110
        (0b0, 0b00110110) => Inst_DS_READ_B32(vdst, vaddr, offset0),
        _ => Inst_INVALID(),
    }
}

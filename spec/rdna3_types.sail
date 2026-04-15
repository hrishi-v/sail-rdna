// --- RDNA3 Hardware Type Definitions ---
$include <prelude.sail>

type DWORD = bits(32)
type QWORD = bits(64)
type sgpr_idx  = bits(7)
type sgpr_src  = bits(8)
type vgpr_idx  = bits(8)
type vop_src   = bits(9)
type lane_id   = bits(5)
type sbase     = bits(6)
type mem_offset_12 = bits(12)

type simm_16 = bits(16)

type offset_21 = bits(21)    // 21-bit offset for SMEM loads
type offset_8  = bits(8)     // 8-bit immediate offset for DS instructions
type soffset_8 = bits(8)     // 8-bit scalar offset for MUBUF

type srsrc_5  = bits(5)      // 5-bit resource constant index (MUBUF)
type seg_2    = bits(2)      // 2-bit memory segment identifier
type opcode_8 = bits(8)      // 8-bit opcode
type flag_1   = bits(1)      // 1-bit boolean flag

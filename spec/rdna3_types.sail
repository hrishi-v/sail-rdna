$include <prelude.sail>

type BYTE = bits(8)
type DWORD = bits(32)
type QWORD = bits(64)

// Operand types — named by semantic role, not instruction format
type sgpr_idx  = bits(7)

// SGPR index (destinations, saddr, soffset, etc.)
type sgpr_src  = bits(8)

// Scalar source encoding (SGPR + inline constants 0-255)
type vgpr_idx  = bits(8)

// VGPR index (0-255)
type vop_src   = bits(9)

// VOP source (scalar range 0-255 + VGPR 256-511)
type lane_id   = bits(5)

// Lane index within a wavefront (0-31)

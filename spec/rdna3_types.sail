$include <prelude.sail>

type SHORT_LENGTH : Int = 16
type DWORD_LENGTH : Int = 32
type QWORD_LENGTH : Int = 64

type BYTE = bits(8)
type SHORT = bits(SHORT_LENGTH)
type DWORD = bits(DWORD_LENGTH)
type QWORD = bits(QWORD_LENGTH)
 
type scalar_dst = bits(7)
type scalar_src = bits(8)

type vector_dst = bits(8)
type vector_src = bits(8)
type vop_src = bits(9)
type vector_lane_id = bits(5)

// FLAT

type flat_offset = bits(12)
type flat_dlc_bit = bits(1)
type flat_glc_bit = bits(1)
type flat_slc_bit = bits(1)
type flat_seg = bits(2)
type flat_op = bits(8)
type flat_addr = bits(8)
type flat_data = bits(8)
type flat_saddr = bits(7)
type flat_sve_bit = bits(1)
type flat_vdst = bits(8)
// Malformed VOP3 v_add_nc_u32 v0, src0=0xFF, src1=0xFF, src2=0
// Hardware grants one literal slot per instruction; encoding two 0xFF
// sources is malformed. Spec gate must reuse the cached literal for
// the second 0xFF, advance PC only once, and not crash.
//
// Layout:
//   .long 0xD5250000  -- VOP3 word 0: enc=110101, opc=v_add_nc_u32 (293), vdst=v0
//   .long 0x0001FEFF  -- VOP3 word 1: src0=0xFF, src1=0xFF, src2=0
//   .long 0x12345678  -- single literal (shared by both 0xFF refs after gate)
//   s_endpgm

.long 0xD5250000
.long 0x0001FEFF
.long 0x12345678
s_endpgm

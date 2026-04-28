; global_load_addr_overlap.asm
; vdst v2 overlaps the addr pair v[2:3]. With no prior pending load on v2
; the address read must see an unencumbered register, so Sail must NOT emit
; a [HAZARD] line. Currently vmem_issue_load(vdst) runs before the address
; reads in global_load_b32, so this fires 32x — one per lane.

v_mov_b32 v2, 0
v_mov_b32 v3, 0
global_load_b32 v2, v[2:3], off offset:0
s_waitcnt vmcnt(0)
s_endpgm

; global_load_addr_pending.asm
; First load makes v2 pending. Second load uses v[2:3] as the address pair
; while v2 is still in-flight — a real RAW hazard. Sail must emit
;   [HAZARD] read of v2 with pending VMEM load
; Reordering vmem_issue_load past the address reads must NOT suppress this.

v_mov_b32 v6, 0
v_mov_b32 v7, 0
global_load_b32 v2, v[6:7], off offset:0
global_load_b32 v8, v[2:3], off offset:0
s_waitcnt vmcnt(0)
s_endpgm

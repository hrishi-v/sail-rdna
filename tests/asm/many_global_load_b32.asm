; vmcnt wrap exploit

v_mov_b32 v2, 0xFEEDFACE
v_mov_b32 v30, 0

global_load_b32 v32, v30, s[24:25] offset:0
global_load_b32 v33, v30, s[24:25] offset:4
global_load_b32 v34, v30, s[24:25] offset:8
global_load_b32 v35, v30, s[24:25] offset:12
global_load_b32 v36, v30, s[24:25] offset:16
global_load_b32 v37, v30, s[24:25] offset:20
global_load_b32 v38, v30, s[24:25] offset:24
global_load_b32 v39, v30, s[24:25] offset:28
global_load_b32 v40, v30, s[24:25] offset:32
global_load_b32 v41, v30, s[24:25] offset:36
global_load_b32 v42, v30, s[24:25] offset:40
global_load_b32 v43, v30, s[24:25] offset:44
global_load_b32 v44, v30, s[24:25] offset:48
global_load_b32 v45, v30, s[24:25] offset:52
global_load_b32 v46, v30, s[24:25] offset:56
global_load_b32 v47, v30, s[24:25] offset:60
global_load_b32 v48, v30, s[24:25] offset:64
global_load_b32 v49, v30, s[24:25] offset:68
global_load_b32 v50, v30, s[24:25] offset:72
global_load_b32 v51, v30, s[24:25] offset:76
global_load_b32 v52, v30, s[24:25] offset:80
global_load_b32 v53, v30, s[24:25] offset:84
global_load_b32 v54, v30, s[24:25] offset:88
global_load_b32 v55, v30, s[24:25] offset:92
global_load_b32 v56, v30, s[24:25] offset:96
global_load_b32 v57, v30, s[24:25] offset:100
global_load_b32 v58, v30, s[24:25] offset:104
global_load_b32 v59, v30, s[24:25] offset:108
global_load_b32 v60, v30, s[24:25] offset:112
global_load_b32 v61, v30, s[24:25] offset:116
global_load_b32 v62, v30, s[24:25] offset:120
global_load_b32 v63, v30, s[24:25] offset:124
global_load_b32 v32, v30, s[24:25] offset:0
global_load_b32 v33, v30, s[24:25] offset:4
global_load_b32 v34, v30, s[24:25] offset:8
global_load_b32 v35, v30, s[24:25] offset:12
global_load_b32 v36, v30, s[24:25] offset:16
global_load_b32 v37, v30, s[24:25] offset:20
global_load_b32 v38, v30, s[24:25] offset:24
global_load_b32 v39, v30, s[24:25] offset:28
global_load_b32 v40, v30, s[24:25] offset:32
global_load_b32 v41, v30, s[24:25] offset:36
global_load_b32 v42, v30, s[24:25] offset:40
global_load_b32 v43, v30, s[24:25] offset:44
global_load_b32 v44, v30, s[24:25] offset:48
global_load_b32 v45, v30, s[24:25] offset:52
global_load_b32 v46, v30, s[24:25] offset:56
global_load_b32 v47, v30, s[24:25] offset:60
global_load_b32 v48, v30, s[24:25] offset:64
global_load_b32 v49, v30, s[24:25] offset:68
global_load_b32 v50, v30, s[24:25] offset:72
global_load_b32 v51, v30, s[24:25] offset:76
global_load_b32 v52, v30, s[24:25] offset:80
global_load_b32 v53, v30, s[24:25] offset:84
global_load_b32 v54, v30, s[24:25] offset:88
global_load_b32 v55, v30, s[24:25] offset:92
global_load_b32 v56, v30, s[24:25] offset:96
global_load_b32 v57, v30, s[24:25] offset:100
global_load_b32 v58, v30, s[24:25] offset:104
global_load_b32 v59, v30, s[24:25] offset:108
global_load_b32 v60, v30, s[24:25] offset:112
global_load_b32 v61, v30, s[24:25] offset:116
global_load_b32 v62, v30, s[24:25] offset:120

; Load 64 — trips vmcnt overflow hazard in Sail; wraps HW vmcnt to 0.
global_load_b32 v2, v30, s[24:25] offset:0

; Snapshot v2 immediately — HW reads stale sentinel, Sail reads mem[0].
v_mov_b32 v5, v2

s_waitcnt vmcnt(0)
s_endpgm

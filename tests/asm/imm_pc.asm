; test body
v_mov_b32 v1, 100
v_add_nc_u32 v2, v1, 200

; epilogue: store results
v_mov_b32 v0, 0x00002008
v_mov_b32 v1, 0x00000000
flat_store_b32 v[0:1], v2
s_endpgm
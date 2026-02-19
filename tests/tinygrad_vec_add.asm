// You act as the host and just put the pointers straight into the registers
s_mov_b64 s[0:1], 0x1000       // Pointer to A
s_mov_b64 s[2:3], 0x2000       // Pointer to B
flat_load_b32 v0, v[0:1]       
flat_load_b32 v1, v[2:3]       
s_waitcnt vmcnt(0) lgkmcnt(0)  
v_add_nc_u32_e64 v2, v0, v1    
flat_store_b32 v[0:1], v2      
s_endpgm
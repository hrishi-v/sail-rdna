s_mov_b32 exec_lo, -1
v_mov_b32 v0, 42
s_branch end_prog
v_mov_b32 v0, 0
end_prog:
s_endpgm

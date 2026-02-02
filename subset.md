# RDNA3 Subset

## Litmus Test-Based Subset

### add_one.asm

```asm
v_mov_b32 v5, 123
v_add_u32 v5, 1, v5
v_mov_b32 %0, v5
```
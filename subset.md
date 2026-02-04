# RDNA3 Subset

## Base Implementation

**VGPRs:** 32-bit, 32-wide, 32 registers []
**SGPRs:** 32-bit,
**LDS (Local Data Store):** 32-bank scratch memory allocated to waves. (128kB)

SIMD Unit = Vector ALU (processes instructions for a single wave(front))

A Compute Unit, contains 2 SIMD32s, with a single path to memory.

Each wave has an EXEC mask (which lanes/threads/work-items are active and not).

Vector memory instructions transfer data between VGPRs and memory. Each work-item supplies its own
memory address and supplies or receives unique data. These instructions are also subject to the EXEC mask.

Initally we don't support 64-wide vector instructions, only 32-wide ones.

## Wave State

PC = Program Counter (48 bits), 2 LSBs are forced to 0.
V0-V255 (VGPRs)

## Litmus Test-Based Subset

### add_one.asm

```asm
v_mov_b32 v5, 123
v_add_u32 v5, 1, v5
v_mov_b32 %0, v5
```
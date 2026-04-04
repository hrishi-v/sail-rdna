"""Test fixture for the read_modify_write kernel.

Describes the AMDHSA kernarg layout, the initial memory / register state
to load into the Sail emulator, and how to parse hardware results.

Kernarg layout (derived from the compiled ASM):
  +0x00 (8B)  global_buffer  →  arr pointer (s_load_b64 s[4:5], s[0:1], 0x0)
  +0x08 (4B)  by_value       →  val         (s_load_b32 s0,     s[0:1], 0x8)
  +0x1c (2B)  hidden         →  group_size_x (s_load_b32 s3,    s[0:1], 0x1c)
"""

from __future__ import annotations

from pathlib import Path

N = 32
VAL = 10

# ── Sail address-space layout ────────────────────────────────────────────────
# Instructions are loaded at 0x0100 by rdna3_emu.
# Keep kernargs and data well clear of the instruction region.
KERNARGS_ADDR = 0x0400
BUF_ADDR = 0x1000


def generate_setup_file(setup_path: Path, dump_output_path: Path) -> None:
    """Write the emulator setup file consumed by ``rdna3_emu --kernel-test``."""
    lines = [
        '# Auto-generated setup for: read_modify_write',
        '#',
        '# AMDHSA register conventions at kernel entry:',
        '#   s[0:1]  = kernarg segment pointer',
        '#   s2      = workgroup_id_x',
        '#   v0      = thread_id within workgroup  (set by GPU runtime)',
        '',
        '# s[0:1] = kernarg segment pointer',
        f'SGPR 0 {KERNARGS_ADDR & 0xFFFFFFFF}',
        f'SGPR 1 {KERNARGS_ADDR >> 32}',
        '# s2 = workgroup_id_x = 0  (single workgroup launch)',
        'SGPR 2 0',
        '',
        '# v0[lane] = threadIdx.x = lane  (provided by the GPU runtime at launch)',
        'VGPR_LANE_ID 0',
        '# v1[lane] = 0  (upper word of the 64-bit workitem index before the shift)',
        'VGPR_CONST 1 0',
        '# Activate all 32 lanes in the wavefront'
        'SGPR 106 0xFFFFFFFF',
        '',
        '# ── Kernel args in Sail memory ───────────────────────────────────────',
        f'MEM32 {KERNARGS_ADDR + 0x00:#010x} {BUF_ADDR & 0xFFFFFFFF:#010x}  # arr ptr lo',
        f'MEM32 {KERNARGS_ADDR + 0x04:#010x} {BUF_ADDR >> 32:#010x}         # arr ptr hi',
        f'MEM32 {KERNARGS_ADDR + 0x08:#010x} {VAL:#010x}                    # val',
        f'MEM32 {KERNARGS_ADDR + 0x1c:#010x} {N:#010x}                      # hidden_group_size_x',
        '',
        '# ── Initial array: arr[i] = i ────────────────────────────────────────',
    ]
    for i in range(N):
        lines.append(f'MEM32 {BUF_ADDR + i * 4:#010x} {i:#010x}')

    lines += [
        '',
        '# ── Dump output array after the kernel executes ─────────────────────',
        f'DUMP_MEM {BUF_ADDR:#010x} {N * 4} {dump_output_path}',
    ]

    setup_path.write_text('\n'.join(lines) + '\n')


def parse_hip_output(results_path: Path) -> list[int]:
    """Parse ``kernels/outputs/read_modify_write_results.log`` → list of N ints."""
    return [
        int(line.strip(), 16)
        for line in results_path.read_text().splitlines()
        if line.strip()
    ]

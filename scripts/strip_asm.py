#!/usr/bin/env python3
"""Strip a HIP-compiled .s file to just the GPU kernel body.

Removes scheduling hints (s_delay_alu, s_clause), assembler directives,
labels, and comments.  Output is a plain RDNA3 assembly file suitable for
assembling with clang or feeding directly to the Sail emulator.

Usage:
    python3 strip_asm.py kernels/asm/foo.s kernels/stripped/foo.asm
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_FUNC_LABEL = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:')

# Instructions that are scheduling / prefetch hints — semantically NOPs in Sail.
_HINT_PREFIXES = ('s_delay_alu', 's_clause')


def extract_kernel_instructions(s_file: Path) -> list[str]:
    """Return the GPU kernel instruction list from a HIP-compiled .s file."""
    lines = s_file.read_text().splitlines()

    in_gpu_bundle = False
    in_function = False
    instructions: list[str] = [
        "\ts_mov_b32 exec_lo, -1  // AUTO-INJECTED: Turn on all 32 lanes"
    ]

    for line in lines:
        stripped = line.strip()

        # Track the GPU offload bundle boundary.
        if '__CLANG_OFFLOAD_BUNDLE____START__ hip-amdgcn' in line:
            in_gpu_bundle = True
            continue
        if '__CLANG_OFFLOAD_BUNDLE____END__ hip-amdgcn' in line:
            break
        if not in_gpu_bundle:
            continue

        # Wait for the mangled function label to begin collecting.
        if not in_function:
            if _FUNC_LABEL.match(line):
                in_function = True
            continue  # skip the label line itself

        # The function body ends when .rodata begins.
        if stripped.startswith('.section'):
            break

        # Drop blank lines, comment lines, directives, and local labels.
        if not stripped:
            continue
        if stripped.startswith(';') or stripped.startswith('#'):
            continue
        if stripped.startswith('.'):
            continue
        if _FUNC_LABEL.match(line):
            continue

        # Drop scheduling / prefetch hints — no semantic effect in Sail.
        if any(stripped.startswith(p) for p in _HINT_PREFIXES):
            continue

        # Strip any trailing inline comment.
        instr = stripped.split(';')[0].rstrip()
        if instr:
            instructions.append(instr)

    return instructions


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(f'usage: {sys.argv[0]} <input.s> [output.asm]')

    s_file = Path(sys.argv[1])
    out_file = (
        Path(sys.argv[2])
        if len(sys.argv) >= 3
        else s_file.parent.parent / 'stripped' / s_file.with_suffix('.asm').name
    )

    instructions = extract_kernel_instructions(s_file)
    if not instructions:
        sys.exit(f'error: no instructions extracted from {s_file}')

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text('\n'.join(instructions) + '\n')
    print(f'Stripped {len(instructions)} instructions → {out_file}')


if __name__ == '__main__':
    main()

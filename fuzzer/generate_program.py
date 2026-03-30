from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    name: str
    asm_lines: tuple[str, ...]
    """Complete body lines — no s_endpgm (added by asm_text())."""


_V_SRC: tuple[str, ...] = ("v1", "v2", "v3")
_S_SRC: tuple[str, ...] = ("s1", "s2", "s3")


def _imm(rng: random.Random) -> str:
    """Inline immediate 0-64: always inline-encoded in RDNA3, never a literal DWORD."""
    return str(rng.randint(0, 64))


def _vr(rng: random.Random) -> str:
    return rng.choice(_V_SRC)


def _sr(rng: random.Random) -> str:
    return rng.choice(_S_SRC)


_InstrFactory = Callable[[random.Random], list[str]]

_INSTRS: list[_InstrFactory] = [
    # pure vector
    lambda rng: [f"v_mov_b32 v0, {_imm(rng)}"],
    lambda rng: [f"v_mov_b32 v0, {_vr(rng)}"],
    lambda rng: [f"v_add_nc_u32_e32 v0, {_imm(rng)}, {_vr(rng)}"],
    lambda rng: [f"v_add_nc_u32_e32 v0, v0, {_vr(rng)}"],
    lambda rng: [f"v_add_nc_u32_e32 v0, {_vr(rng)}, {_vr(rng)}"],
    lambda rng: [f"s_mov_b32 s0, {_imm(rng)}", "v_mov_b32 v0, s0"],
    lambda rng: [f"s_add_u32 s0, {_sr(rng)}, {_imm(rng)}", "v_mov_b32 v0, s0"],
    lambda rng: [f"s_add_u32 s0, {_sr(rng)}, {_sr(rng)}", "v_mov_b32 v0, s0"],
    lambda rng: [f"s_sub_u32 s0, {_sr(rng)}, {_imm(rng)}", "v_mov_b32 v0, s0"],
]


def _preamble(rng: random.Random) -> list[str]:
    """Initialise all working registers before the body to avoid UB."""
    return [
        "s_mov_b32 exec_lo, -1",
        f"v_mov_b32 v1, {rng.randint(0, 64)}",
        f"v_mov_b32 v2, {rng.randint(0, 64)}",
        f"v_mov_b32 v3, {rng.randint(0, 64)}",
        f"s_mov_b32 s1, {rng.randint(0, 64)}",
        f"s_mov_b32 s2, {rng.randint(0, 64)}",
        f"s_mov_b32 s3, {rng.randint(0, 64)}",
    ]


def generate_program(
    rng: random.Random,
    name: str,
    n_instrs: int = 5,
) -> Program:
    lines: list[str] = _preamble(rng)
    for _ in range(n_instrs):
        lines.extend(rng.choice(_INSTRS)(rng))
    return Program(name=name, asm_lines=tuple(lines))



def asm_text(prog: Program) -> str:
    """Sail-compatible .asm file (one instruction per line, s_endpgm appended)."""
    return "\n".join(prog.asm_lines) + "\ns_endpgm\n"


def hip_inc_text(prog: Program) -> str:
    """HIP .inc file — each line as a C string literal for use in asm volatile."""
    return "".join(f'"{line}\\n\\t"\n' for line in prog.asm_lines)


def hip_dump_inc_text() -> str:
    """HIP dump .inc — always captures v0 via flat_store_b32."""
    return (
        '"v_mov_b32 v14, %0\\n\\t"\n'
        '"v_mov_b32 v15, %1\\n\\t"\n'
        '"flat_store_b32 v[14:15], v0\\n\\t"\n'
        '"s_waitcnt vmcnt(0)\\n\\t"\n'
    )

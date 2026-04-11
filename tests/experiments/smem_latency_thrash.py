#!/usr/bin/env python3
"""
SMEM load latency under extreme scalar-cache (K$) capacity pressure.

Hypothesis: the 46-cycle s_load_b32 crossover measured in
s_load_b32_latency.py is the cache-hit latency.  By thrashing
the entire 16 KB RDNA3 Scalar L1 before the target load we force a
capacity miss and expect a significantly higher crossover.

Strategy per probe:
  1. s_dcache_inv                              — cold start
  2. Prime: s_load_b32 target addr, waitcnt    — pull target line in
  3. Thrash: 256× s_load_b128 from s[20:21]
            with offsets [0, 64, 128, …, 16320] — evict every line
  4. s_waitcnt lgkmcnt(0)                      — drain thrash
  5. s_load_b32 s2, s[24:25], 0x0              — target (capacity miss)
  6. <N × fill instructions>                   — variable delay
  7. v_mov_b32 v0, s2                          — speculative snapshot
  8. s_waitcnt lgkmcnt(0)
  9. v_mov_b32 v1, s2                          — ground truth

Run from repo root:
    python tests/experiments/smem_latency_thrash.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT    = Path(__file__).resolve().parents[2]
HARNESS_BIN  = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"
INCLUDE_DIR  = REPO_ROOT / "bare_metal_test" / "harness" / "include"
KERNEL_HIP   = REPO_ROOT / "bare_metal_test" / "harness" / "kernel.hip"
OUTPUTS_DIR  = REPO_ROOT / "outputs"

BUILD_DIR    = REPO_ROOT / "build" / "smem_thrash_experiment"
INC_DIR      = BUILD_DIR / "inc"
CO_DIR       = BUILD_DIR / "co"
DUMP_INC_DIR = BUILD_DIR / "dump_inc"
MANIFEST_DIR = BUILD_DIR / "manifests"

POISON           = 0x11111111
N_MAX            = 400
SNOP_CROSSOVER   = 46   # baseline cache-hit reference

# 16 KB = 16384 bytes.  s_load_b128 reads 16 bytes per instruction.
# We need 16384 / 16 = 1024 loads to sweep the full cache.
# Use a stride of 64 bytes (one cache line) so each load evicts a
# different line: 16384 / 64 = 256 loads.
THRASH_LOADS     = 256
THRASH_STRIDE    = 64    # bytes between each s_load_b128

# We over-provision the vgpr_out buffer (s[20:21]) so that the
# thrashing s_load_b128 reads at offsets [0..16320] all land inside a
# valid HIP allocation.  130 vgprs × 32 lanes × 4 B = 16640 B > 16 KB.
VGPR_ALLOC_COUNT = 130

# ---------------------------------------------------------------------------
# Fill type definitions
# ---------------------------------------------------------------------------

def _rep(instr: str) -> Callable[[int], list[str]]:
    return lambda n: [instr] * n

def _alt(a: str, b: str) -> Callable[[int], list[str]]:
    def _gen(n: int) -> list[str]:
        out: list[str] = []
        for _ in range(n):
            out += [a, b]
        return out
    return _gen

FILLS: list[tuple[str, str, Callable[[int], list[str]]]] = [
    ("s_nop 0",                    "snop",   _rep("s_nop 0")),
    ("v_nop",                      "vnop",   _rep("v_nop")),
    ("s_add_u32 s4,s4,1",          "sadd",   _rep("s_add_u32 s4, s4, 1")),
    ("s_and_b32 s4,s4,s4",         "sand",   _rep("s_and_b32 s4, s4, s4")),
    ("v_add_f32 v3,v3,v3",         "vaddf",  _rep("v_add_f32 v3, v3, v3")),
    ("v_add_u32 v3,v3,v3",         "vaddu",  _rep("v_add_u32 v3, v3, v3")),
    ("v_mul_f32 v3,v3,v3",         "vmulf",  _rep("v_mul_f32 v3, v3, v3")),
    ("v_mov_b32 v3,v3",            "vmov",   _rep("v_mov_b32 v3, v3")),
    ("mixed(s_add+v_add_f32)/iter","mixed",  _alt("s_add_u32 s4, s4, 1", "v_add_f32 v3, v3, v3")),
]

# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------

def _make_thrash_block() -> list[str]:
    """Generate 256 s_load_b128 instructions that sweep 16 KB via s[20:21].

    Destination SGPRs rotate through s[12:15] and s[16:19] so we only
    need two quad-aligned SGPR groups and don't clobber anything important.
    """
    lines: list[str] = []
    dst_groups = ["s[12:15]", "s[16:19]"]
    for i in range(THRASH_LOADS):
        dst = dst_groups[i % 2]
        offset = i * THRASH_STRIDE
        lines.append(f"s_load_b128 {dst}, s[20:21], {offset:#x}")
    return lines


def _make_inc(fill_instrs: list[str]) -> str:
    thrash = _make_thrash_block()
    fill   = "".join(f'"{i}\\n\\t"\n' for i in fill_instrs)
    thrash_asm = "".join(f'"{i}\\n\\t"\n' for i in thrash)

    return (
        '"s_dcache_inv\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        '"s_load_b32 s2, s[24:25], 0x0\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'

        + thrash_asm +
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        '"s_mov_b32 s2, 0x11111111\\n\\t"\n'
        '"s_load_b32 s2, s[24:25], 0x0\\n\\t"\n'
        + fill +
        '"v_mov_b32 v0, s2\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        '"v_mov_b32 v1, s2\\n\\t"'
    )


def _make_manifest(name: str, co_path: Path) -> dict:
    # Provide 1 DWORD of target data for the s_load_b32 at s[24:25]+0.
    # The thrashing reads from s[20:21] which points at the vgpr_out
    # allocation — already valid GPU memory, no extra init needed.
    return {
        "name": name,
        "capture_prefix": "v",
        "initial_memory_hex": ["deadbeef"],
        "registers": {
            "vgprs": {
                "count": VGPR_ALLOC_COUNT,
                "indices": [0, 1],
            },
            "sgprs": {"count": 0, "indices": []},
        },
        "binary_path": str(co_path),
    }


def _make_dump_inc(manifest: dict) -> str:
    lines = [
        "s_waitcnt vmcnt(0) lgkmcnt(0)",
        "s_waitcnt_vscnt null, 0",
        "s_mov_b32 exec_lo, -1",
        "v_mbcnt_lo_u32_b32 v30, -1, 0",
        "v_lshlrev_b32 v30, 2, v30",
    ]
    for i, reg_idx in enumerate(manifest["registers"]["vgprs"]["indices"]):
        offset = i * 128
        lines += [
            f"v_add_co_u32 v31, vcc_lo, {offset}, v30",
            "v_add_co_u32 v31, vcc_lo, s20, v31",
            "v_add_co_ci_u32_e64 v32, null, s21, 0, vcc_lo",
            f"global_store_b32 v[31:32], v{reg_idx}, off",
            "s_waitcnt_vscnt null, 0",
        ]
    return "\n".join(f'"{line}\\n\\t"' for line in lines)

# ---------------------------------------------------------------------------
# Build / run / probe
# ---------------------------------------------------------------------------

def _run(cmd: list[str], label: str) -> None:
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"ERROR: {label} failed\n{r.stderr.decode()}")


def _probe(slug: str, instrs: list[str]) -> bool:
    """Return True if v0 is FRESH (load resolved before waitcnt)."""
    name          = f"thrash_{slug}_{len(instrs):04d}"
    inc_path      = INC_DIR      / f"{name}.inc"
    dump_inc_path = DUMP_INC_DIR / f"{name}_dump.inc"
    co_path       = CO_DIR       / f"{name}.co"
    manifest_path = MANIFEST_DIR / f"{name}.json"

    manifest = _make_manifest(name, co_path)

    if not co_path.exists():
        inc_path.write_text(_make_inc(instrs))
        dump_inc_path.write_text(_make_dump_inc(manifest))
        manifest_path.write_text(json.dumps(manifest))
        _run([
            "hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
            f"-I{INCLUDE_DIR.resolve()}",
            f'-DTEST_INC="{inc_path.resolve()}"',
            f'-DDUMP_INC="{dump_inc_path.resolve()}"',
            str(KERNEL_HIP), "-o", str(co_path),
        ], f"hipcc {name}")
    elif not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest))

    _run([str(HARNESS_BIN), str(manifest_path)], f"harness {name}")

    out = OUTPUTS_DIR / f"{name}_vector_registers"
    for line in out.read_text().splitlines():
        if line.strip().startswith("v0:"):
            return int(line.split()[1], 16) != POISON
    return False


def _bisect(label: str, slug: str, gen: Callable[[int], list[str]]) -> int | None:
    """Return minimum N where v0 is FRESH, or None if still STALE at N_MAX."""
    print(f"  probe N=0 ... ", end="", flush=True)
    if _probe(slug, gen(0)):
        print("FRESH"); return 0
    print("stale", flush=True)

    print(f"  probe N={N_MAX} ... ", end="", flush=True)
    if not _probe(slug, gen(N_MAX)):
        print("stale"); return None
    print("FRESH", flush=True)

    lo, hi = 0, N_MAX
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        print(f"  probe N={mid} ... ", end="", flush=True)
        fresh = _probe(slug, gen(mid))
        print("FRESH" if fresh else "stale", flush=True)
        if fresh:
            hi = mid
        else:
            lo = mid
    return hi

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not HARNESS_BIN.exists():
        sys.exit(f"ERROR: harness binary not found at {HARNESS_BIN}")

    for d in (INC_DIR, CO_DIR, DUMP_INC_DIR, MANIFEST_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  SMEM Latency under 16 KB K$ Capacity Pressure")
    print(f"  Thrashing block: {THRASH_LOADS} × s_load_b128, stride {THRASH_STRIDE} B")
    print(f"  Bisection range: N ∈ [0, {N_MAX}]")
    print("=" * 72)

    results: list[tuple[str, int | None]] = []
    for display, slug, gen in FILLS:
        print(f"\n[{display}]", flush=True)
        cx = _bisect(display, slug, gen)
        results.append((display, cx))

    ref = SNOP_CROSSOVER
    print()
    print(f"{'Fill (N = iterations)':<35}  {'crossover N':>11}  {'cyc/iter':>8}  "
          f"{'Δ vs hit':>8}  note")
    print("-" * 80)
    for display, cx in results:
        cx_str = str(cx) if cx is not None else f"> {N_MAX}"
        if cx is None:
            cyc_str = f"< {ref/N_MAX:.1f}"
            delta   = "—"
            note    = ""
        elif cx == 0:
            cyc_str = "inf"
            delta   = "—"
            note    = "already fresh at N=0"
        else:
            cyc_per = ref / cx
            cyc_str = f"{cyc_per:.1f}"
            delta   = f"{cx - ref:+d}" if cx != ref else "0"
            note    = "(2 instrs/iter)" if display.startswith("mixed") else ""
        print(f"{display:<35}  {cx_str:>11}  {cyc_str:>8}  {delta:>8}  {note}")

    print()
    print(f"Reference: s_nop 0 cache-hit crossover = {ref}")
    print("Δ vs hit = thrash_crossover − hit_crossover (positive = extra latency)")

if __name__ == "__main__":
    main()

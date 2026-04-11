#!/usr/bin/env python3
"""
SMEM cache-pressure sweep: bisect s_load_b32 crossover latency at
variable levels of L1 scalar-cache (K$) thrashing and export to CSV.

Sweeps THRASH_AMOUNTS = [0, 64, 128, 256, 512, 1024, 2048] where each
unit is one s_load_b128 (16 B).  1024 loads ≈ 16 KB ≈ full K$ capacity.

Run from repo root:
    python tests/experiments/smem_cache_sweep.py
"""
from __future__ import annotations

import csv
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

BUILD_DIR    = REPO_ROOT / "build" / "smem_sweep_experiment"
INC_DIR      = BUILD_DIR / "inc"
CO_DIR       = BUILD_DIR / "co"
DUMP_INC_DIR = BUILD_DIR / "dump_inc"
MANIFEST_DIR = BUILD_DIR / "manifests"
CSV_PATH     = OUTPUTS_DIR / "cache_pressure_sweep.csv"

POISON           = 0x11111111
N_MAX            = 400
SNOP_CROSSOVER   = 46

THRASH_AMOUNTS   = [0, 64, 128, 256, 512, 1024, 2048]
THRASH_STRIDE    = 0x10  # 16 bytes per s_load_b128, sequential

# Max footprint: 2048 * 16 = 32768 bytes.
# vgpr_out allocation = count * 32 lanes * 4 B = count * 128 B.
# Need count >= 32768 / 128 = 256.  Use 260 for headroom.
VGPR_ALLOC_COUNT = 260

# Pad initial_memory_hex to cover max(THRASH_AMOUNTS) * 16 bytes = 8192
# DWORDs so the manifest documents the full address range even though the
# universal harness caps its mem_buf at 64 ints (the thrash reads go
# through the vgpr_out buffer at s[20:21] instead).
_MAX_MEM_DWORDS  = max(THRASH_AMOUNTS) * 16 // 4  # 8192

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

def _make_thrash_block(thrash_count: int) -> list[str]:
    """Generate `thrash_count` s_load_b128 instructions at stride 0x10."""
    lines: list[str] = []
    dst_groups = ["s[12:15]", "s[16:19]"]
    for i in range(thrash_count):
        dst = dst_groups[i % 2]
        offset = i * THRASH_STRIDE
        lines.append(f"s_load_b128 {dst}, s[20:21], {offset:#x}")
    return lines


def _make_inc(thrash_count: int, fill_instrs: list[str]) -> str:
    thrash = _make_thrash_block(thrash_count)
    fill_asm   = "".join(f'"{i}\\n\\t"\n' for i in fill_instrs)
    thrash_asm = "".join(f'"{i}\\n\\t"\n' for i in thrash)

    parts: list[str] = [
        # 1. Invalidate scalar cache – cold start
        '"s_dcache_inv\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n',
    ]

    if thrash_count > 0:
        # 2. Prime target line into K$
        parts.append(
            '"s_load_b32 s2, s[24:25], 0x0\\n\\t"\n'
            '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        )
        # 3. Thrash block
        parts.append(thrash_asm)
        # 4. Drain thrash loads
        parts.append('"s_waitcnt lgkmcnt(0)\\n\\t"\n')

    # 5. Poison + target load
    parts.append(
        '"s_mov_b32 s2, 0x11111111\\n\\t"\n'
        '"s_load_b32 s2, s[24:25], 0x0\\n\\t"\n'
    )

    # 6. Variable fill
    parts.append(fill_asm)

    # 7. Speculative snapshot
    parts.append('"v_mov_b32 v0, s2\\n\\t"\n')

    # 8-9. Wait + ground truth
    parts.append(
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        '"v_mov_b32 v1, s2\\n\\t"'
    )

    return "".join(parts)


def _make_manifest(name: str, co_path: Path) -> dict:
    mem_hex = ["deadbeef"] + ["00000000"] * (_MAX_MEM_DWORDS - 1)
    return {
        "name": name,
        "capture_prefix": "v",
        "initial_memory_hex": mem_hex,
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


def _probe(thrash_count: int, slug: str, instrs: list[str]) -> bool:
    """Return True if v0 is FRESH (load resolved before waitcnt)."""
    name          = f"sweep_t{thrash_count:04d}_{slug}_{len(instrs):04d}"
    inc_path      = INC_DIR      / f"{name}.inc"
    dump_inc_path = DUMP_INC_DIR / f"{name}_dump.inc"
    co_path       = CO_DIR       / f"{name}.co"
    manifest_path = MANIFEST_DIR / f"{name}.json"

    manifest = _make_manifest(name, co_path)

    if not co_path.exists():
        inc_path.write_text(_make_inc(thrash_count, instrs))
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


def _bisect(
    thrash_count: int,
    label: str,
    slug: str,
    gen: Callable[[int], list[str]],
) -> int | None:
    """Return minimum N where v0 is FRESH, or None if still STALE at N_MAX."""
    print(f"  probe N=0 ... ", end="", flush=True)
    if _probe(thrash_count, slug, gen(0)):
        print("FRESH"); return 0
    print("stale", flush=True)

    print(f"  probe N={N_MAX} ... ", end="", flush=True)
    if not _probe(thrash_count, slug, gen(N_MAX)):
        print("stale"); return None
    print("FRESH", flush=True)

    lo, hi = 0, N_MAX
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        print(f"  probe N={mid} ... ", end="", flush=True)
        fresh = _probe(thrash_count, slug, gen(mid))
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

    print("=" * 76)
    print("  SMEM Cache-Pressure Sweep")
    print(f"  Thrash levels (s_load_b128 count): {THRASH_AMOUNTS}")
    print(f"  Stride per load: {THRASH_STRIDE:#x} ({THRASH_STRIDE} B)")
    print(f"  Bisection range: N ∈ [0, {N_MAX}]")
    print(f"  CSV output: {CSV_PATH}")
    print("=" * 76)

    all_results: list[tuple[int, str, int | None]] = []

    with open(CSV_PATH, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Fill_Type", "Thrash_Count", "Crossover_N"])

        for thrash_count in THRASH_AMOUNTS:
            footprint_kb = thrash_count * THRASH_STRIDE / 1024
            print(f"\n{'─' * 76}")
            print(f"  Thrash level: {thrash_count} loads "
                  f"({footprint_kb:.1f} KB footprint)")
            print(f"{'─' * 76}")

            for display, slug, gen in FILLS:
                print(f"\n  [{display}]", flush=True)
                cx = _bisect(thrash_count, display, slug, gen)
                all_results.append((thrash_count, display, cx))

                cx_csv = cx if cx is not None else ""
                writer.writerow([display, thrash_count, cx_csv])
                csvfile.flush()

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    ref = SNOP_CROSSOVER
    fill_names = [d for d, _, _ in FILLS]

    print(f"\n\n{'=' * 76}")
    print("  Summary: Crossover N per (Fill × Thrash Level)")
    print(f"{'=' * 76}\n")

    header = f"{'Fill':<35}" + "".join(f"  {t:>6}" for t in THRASH_AMOUNTS)
    print(header)
    print("-" * len(header))

    lookup: dict[tuple[int, str], int | None] = {
        (tc, d): cx for tc, d, cx in all_results
    }

    for display in fill_names:
        cells = []
        for tc in THRASH_AMOUNTS:
            cx = lookup.get((tc, display))
            cells.append(f"  {cx if cx is not None else '>'+str(N_MAX):>6}")
        print(f"{display:<35}" + "".join(cells))

    print()
    print(f"Reference: s_nop 0 cache-hit crossover = {ref}")
    print(f"CSV written to: {CSV_PATH}")


if __name__ == "__main__":
    main()

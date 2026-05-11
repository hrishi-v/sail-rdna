#!/usr/bin/env python3
"""
Load-latency × cache-pressure × payload-size sweep.

For each (payload ∈ {b32,b64,b128}, cache-pressure ∈ THRASH_AMOUNTS,
fill-type ∈ FILLS), bisects the smallest NOP-fill count N at which the
load is observed FRESH ≥ 99 % of the time over 100 internal iterations.

Each kernel runs a 100-iteration loop internally (compile-once, run-once
per probe) so total harness invocations stay around ~1.7K rather than
~590K.  Within each iteration:

    s_dcache_inv          ; cold start
    [ prime + thrash ]    ; controlled K$ pressure
    poison destination
    target s_load
    N × fill instructions
    speculative v_mov     ; snapshot s_dst into VGPR
    s_waitcnt lgkmcnt(0)  ; drain
    if snapshot != poison: counter++

Outputs:
    outputs/load_latency_by_payload_and_pressure.csv   (per-probe success)
    outputs/load_latency_crossover.csv                 (derived crossover-N)

Run from repo root:
    python tests/experiments/load_latency_by_payload_and_pressure.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT    = Path(__file__).resolve().parents[2]
HARNESS_BIN  = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"
INCLUDE_DIR  = REPO_ROOT / "bare_metal_test" / "harness" / "include"
KERNEL_HIP   = REPO_ROOT / "bare_metal_test" / "harness" / "kernel.hip"
OUTPUTS_DIR  = REPO_ROOT / "outputs"
RESULTS_DIR  = REPO_ROOT / "tests" / "experiments" / "results"

BUILD_DIR    = REPO_ROOT / "build" / "load_lat_pressure_payload"
INC_DIR      = BUILD_DIR / "inc"
CO_DIR       = BUILD_DIR / "co"
DUMP_INC_DIR = BUILD_DIR / "dump_inc"
MANIFEST_DIR = BUILD_DIR / "manifests"

RAW_CSV         = OUTPUTS_DIR / "load_latency_by_payload_and_pressure.csv"
CROSSOVER_CSV   = OUTPUTS_DIR / "load_latency_crossover.csv"

POISON          = 0x11111111
ITERATIONS      = 100
SUCCESS_CUTOFF  = 99    # crossover := smallest N with successes >= 99
N_MAX           = 150
THRASH_AMOUNTS  = [0, 64, 128, 256, 512, 1024, 2048]
THRASH_STRIDE   = 0x10

# vgpr_out buffer size (per-lane × per-vgpr-index): need to cover thrash
# footprint = 2048 * 16 = 32768 B.  count * 32 lanes * 4 B = count * 128 B.
VGPR_ALLOC_COUNT = 260
_MAX_MEM_DWORDS  = max(THRASH_AMOUNTS) * 16 // 4  # 8192

# ---------------------------------------------------------------------------
# Fill types — match existing s_load_b{32,64,128}_latency scripts
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
# Payload descriptors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Payload:
    label:        str          # "b32" / "b64" / "b128"
    load_instr:   str          # "s_load_b32" / etc
    dst_regs:     list[int]    # SGPR indices written by load
    dst_operand:  str          # asm operand string, e.g. "s2" or "s[2:3]"
    snap_vgprs:   list[int]    # VGPRs that snapshot each dst SGPR

PAYLOADS: list[Payload] = [
    Payload("b32",  "s_load_b32",  [2],            "s2",       [0]),
    Payload("b64",  "s_load_b64",  [2, 3],         "s[2:3]",   [0, 1]),
    Payload("b128", "s_load_b128", [8, 9, 10, 11], "s[8:11]",  [0, 1, 2, 3]),
]

# ---------------------------------------------------------------------------
# Asm fragment helpers
# ---------------------------------------------------------------------------

def _emit_thrash(thrash_count: int) -> list[str]:
    """K$-thrash: thrash_count s_load_b128 across vgpr_out buffer at stride 16 B."""
    if thrash_count == 0:
        return []
    lines: list[str] = []
    dst_groups = ["s[12:15]", "s[16:19]"]
    for i in range(thrash_count):
        dst = dst_groups[i % 2]
        offset = i * THRASH_STRIDE
        lines.append(f"s_load_b128 {dst}, s[20:21], {offset:#x}")
    return lines


def _emit_iteration(payload: Payload, thrash_count: int, fill: list[str]) -> list[str]:
    """One loop body. Always primes target line, then optional thrash,
    then poison + target load + fill + speculative read + drain + check.

    The single `s_dcache_inv` lives outside the loop (kernel-startup), so
    cache state is reset once and every iter follows the same prime-then-
    thrash-then-load path. This keeps every iter's latency comparable.
    """
    out: list[str] = []

    # Prime target line into K$ — keeps iter-1 and iter-N on the same path.
    out += [f"{payload.load_instr} {payload.dst_operand}, s[24:25], 0x0",
            "s_waitcnt lgkmcnt(0)"]

    if thrash_count > 0:
        out += _emit_thrash(thrash_count)
        out += ["s_waitcnt lgkmcnt(0)"]

    # Poison every destination SGPR
    for sg in payload.dst_regs:
        out.append(f"s_mov_b32 s{sg}, 0x11111111")

    # Issue target load
    out.append(f"{payload.load_instr} {payload.dst_operand}, s[24:25], 0x0")

    # Fill (latency hider under test)
    out += list(fill)

    # Speculative snapshot — BEFORE waitcnt, this is the latency probe
    for sg, vg in zip(payload.dst_regs, payload.snap_vgprs):
        out.append(f"v_mov_b32 v{vg}, s{sg}")

    # Drain so next iter's prime starts cleanly
    out.append("s_waitcnt lgkmcnt(0)")

    # Freshness check: success iff *every* snapshot != poison.
    first = payload.snap_vgprs[0]
    out += [
        f"v_cmp_ne_u32 vcc_lo, 0x11111111, v{first}",
        "v_cndmask_b32 v9, 0, 1, vcc_lo",
    ]
    for vg in payload.snap_vgprs[1:]:
        out += [
            f"v_cmp_ne_u32 vcc_lo, 0x11111111, v{vg}",
            "v_cndmask_b32 v10, 0, 1, vcc_lo",
            "v_and_b32 v9, v9, v10",
        ]
    out.append("v_add_nc_u32 v8, v8, v9")
    return out


def _make_inc(payload: Payload, thrash_count: int, fill: list[str]) -> str:
    """Generate the inline-asm body inserted via #include TEST_INC."""
    pre: list[str] = [
        "v_mov_b32 v8, 0",
        f"s_movk_i32 s28, {ITERATIONS}",
        "s_dcache_inv",                    # one cold start before the loop
        "s_waitcnt lgkmcnt(0)",
        ".Lloop_start:",
    ]
    body = _emit_iteration(payload, thrash_count, fill)
    post: list[str] = [
        "s_sub_i32 s28, s28, 1",
        "s_cmp_lg_u32 s28, 0",
        "s_cbranch_scc1 .Lloop_start",
    ]
    instrs = pre + body + post
    return "".join(f'"{i}\\n\\t"\n' for i in instrs)


def _make_manifest(name: str, co_path: Path) -> dict:
    mem_hex = ["deadbeef", "cafebabe", "12345678", "87654321"]
    if _MAX_MEM_DWORDS > len(mem_hex):
        mem_hex += ["00000000"] * (_MAX_MEM_DWORDS - len(mem_hex))
    return {
        "name": name,
        "capture_prefix": "v",
        "initial_memory_hex": mem_hex,
        "registers": {
            "vgprs": {"count": VGPR_ALLOC_COUNT, "indices": [8]},
            "sgprs": {"count": 0, "indices": []},
        },
        "binary_path": str(co_path),
    }


def _make_dump_inc(manifest: dict) -> str:
    """Dump v8 (success counter) to vgpr_out — re-enables full exec mask first."""
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


def _probe(payload: Payload, thrash_count: int, fill_slug: str,
           gen: Callable[[int], list[str]], n: int) -> int:
    """Compile + run kernel; return success count [0..ITERATIONS]."""
    name = f"lat_{payload.label}_t{thrash_count:04d}_{fill_slug}_n{n:04d}"
    inc_path      = INC_DIR      / f"{name}.inc"
    dump_inc_path = DUMP_INC_DIR / f"{name}_dump.inc"
    co_path       = CO_DIR       / f"{name}.co"
    manifest_path = MANIFEST_DIR / f"{name}.json"

    manifest = _make_manifest(name, co_path)

    if not co_path.exists():
        inc_path.write_text(_make_inc(payload, thrash_count, gen(n)))
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
        if line.strip().startswith("v8:"):
            return int(line.split()[1], 16)
    sys.exit(f"ERROR: v8 not found in {out}")


def _bisect_crossover(payload: Payload, thrash_count: int, fill_slug: str,
                      gen: Callable[[int], list[str]],
                      record: Callable[[int, int], None]) -> int | None:
    """Smallest N with success_count ≥ SUCCESS_CUTOFF, or None if never reached."""
    s0 = _probe(payload, thrash_count, fill_slug, gen, 0)
    record(0, s0)
    print(f"    N=0   ⇒ {s0}/{ITERATIONS}", flush=True)
    if s0 >= SUCCESS_CUTOFF:
        return 0

    sN = _probe(payload, thrash_count, fill_slug, gen, N_MAX)
    record(N_MAX, sN)
    print(f"    N={N_MAX} ⇒ {sN}/{ITERATIONS}", flush=True)
    if sN < SUCCESS_CUTOFF:
        return None

    lo, hi = 0, N_MAX
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        sm = _probe(payload, thrash_count, fill_slug, gen, mid)
        record(mid, sm)
        print(f"    N={mid:<3} ⇒ {sm}/{ITERATIONS}", flush=True)
        if sm >= SUCCESS_CUTOFF:
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

    for d in (INC_DIR, CO_DIR, DUMP_INC_DIR, MANIFEST_DIR, OUTPUTS_DIR,
              RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("  Load latency × cache pressure × payload size")
    print(f"  Payloads:         {[p.label for p in PAYLOADS]}")
    print(f"  Pressure levels:  {THRASH_AMOUNTS}")
    print(f"  Fill types:       {len(FILLS)}")
    print(f"  Iterations/probe: {ITERATIONS}, cutoff ≥ {SUCCESS_CUTOFF}")
    print(f"  Bisection range:  N ∈ [0, {N_MAX}]")
    print(f"  Raw CSV:          {RAW_CSV}")
    print(f"  Crossover CSV:    {CROSSOVER_CSV}")
    print("=" * 78)

    crossover_rows: list[tuple[str, int, str, int | None]] = []

    raw_f = open(RAW_CSV, "w", newline="")
    raw_w = csv.writer(raw_f)
    raw_w.writerow(["payload_size", "cache_pressure", "fill_type",
                    "nop_count", "iterations", "successes", "success_rate"])

    try:
        for payload in PAYLOADS:
            for thrash_count in THRASH_AMOUNTS:
                kb = thrash_count * THRASH_STRIDE / 1024
                print(f"\n── {payload.label} · pressure {thrash_count} "
                      f"({kb:.1f} KB footprint) ──", flush=True)
                for display, slug, gen in FILLS:
                    print(f"  [{display}]", flush=True)

                    def record(n: int, s: int,
                               _p=payload, _tc=thrash_count, _d=display) -> None:
                        raw_w.writerow([_p.label, _tc, _d, n, ITERATIONS, s,
                                        f"{s/ITERATIONS:.3f}"])
                        raw_f.flush()

                    cx = _bisect_crossover(payload, thrash_count, slug, gen, record)
                    crossover_rows.append((payload.label, thrash_count, display, cx))
                    print(f"    crossover-N: {cx}", flush=True)
    finally:
        raw_f.close()

    with open(CROSSOVER_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["payload_size", "cache_pressure", "fill_type", "crossover_n"])
        for label, tc, display, cx in crossover_rows:
            w.writerow([label, tc, display, "" if cx is None else cx])

    # Mirror copies under tests/experiments/results/
    for src in (RAW_CSV, CROSSOVER_CSV):
        dst = RESULTS_DIR / src.name
        dst.write_bytes(src.read_bytes())

    print(f"\nDone. Raw → {RAW_CSV}\n      Crossover → {CROSSOVER_CSV}")


if __name__ == "__main__":
    main()

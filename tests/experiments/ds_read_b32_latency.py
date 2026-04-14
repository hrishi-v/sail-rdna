#!/usr/bin/env python3
"""
LDS bank-conflict latency sweep for ds_read_b32 on GFX1101 (RDNA3).

Measures the per-instruction RTC-tick cost of ds_read_b32 for each conflict
degree by sweeping stride multipliers [4, 8, 16, 32, 64, 128] bytes/lane,
which produce [1, 2, 4, 8, 16, 32]-way bank conflicts respectively.

Bank math:
    bank(lane) = (lane_id * stride_bytes / 4) % 32
    conflict_ways = gcd(stride_bytes // 4, 32)

Method (two-point slope, identical to timer_calibration.py):
    For each stride, compile and run kernels with N_LO and N_HI ds_read_b32
    instructions.  The payload uses 16 rotating destination VGPRs (v10-v25)
    to avoid WAW scoreboard serialization while keeping the loads live via
    a post-timing XOR anchor into v0.

    ticks_per_read = (median_ticks_hi - median_ticks_lo) / (N_HI - N_LO)

    This cancels out fixed overhead (timer setup, pipeline drain, etc.) and
    defeats RTC quantization noise by using large iteration counts.

Output:
  - Console table of (stride, ways, ticks_per_read)
  - A ready-to-paste Sail snippet to replace the lds_penalty_cycles arms
    in spec/execute/rdna3_ds_execute.sail

Prerequisites:
  - bare_metal_test/harness/kernel.hip must have the amdgpu_lds_size(4096)
    attribute (already added by the ds_read_b32 implementation commit).
  - The universal_harness binary must be built.

Run from repo root:
    python tests/experiments/ds_read_b32_latency.py
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from math import gcd
from pathlib import Path

REPO_ROOT    = Path(__file__).resolve().parents[2]
HARNESS_BIN  = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"
INCLUDE_DIR  = REPO_ROOT / "bare_metal_test" / "harness" / "include"
KERNEL_HIP   = REPO_ROOT / "bare_metal_test" / "harness" / "kernel.hip"
OUTPUTS_DIR  = REPO_ROOT / "outputs"

BUILD_DIR    = REPO_ROOT / "build" / "ds_latency_experiment"
INC_DIR      = BUILD_DIR / "inc"
CO_DIR       = BUILD_DIR / "co"
DUMP_INC_DIR = BUILD_DIR / "dump_inc"
MANIFEST_DIR = BUILD_DIR / "manifests"

# Strides to sweep.  stride_bytes / 4 = DWORDs per lane step.
# conflict_ways = gcd(stride_bytes // 4, 32)
STRIDES: list[int] = [4, 8, 16, 32, 64, 128]

# Two-point slope parameters (same methodology as timer_calibration.py).
N_LO: int = 1000
N_HI: int = 5000

# How many independent harness runs per (stride, N) pair for noise reduction.
RUNS_PER_POINT: int = 5

# VGPRs captured per run.
#   v0  = XOR anchor of ds_read_b32 results (sanity: should be 0 for even N)
#   v1  = copy of v0
#   v4  = timer delta, bits [31:0]   (GPU-side s_sub_u32)
#   v5  = timer delta, bits [63:32]  (GPU-side s_subb_u32)
VGPR_INDICES = [0, 1, 4, 5]

# Rotating destination VGPRs for the timed payload (avoids WAW serialization).
DEST_VGPRS = list(range(10, 26))  # v10 through v25 (16 registers)

DEADBEEF = 0xDEADBEEF


# ---------------------------------------------------------------------------
# Conflict-degree helper
# ---------------------------------------------------------------------------

def conflict_ways(stride_bytes: int) -> int:
    """Return number of lanes sharing the worst-case LDS bank."""
    dwords = stride_bytes // 4
    return gcd(dwords, 32)


# ---------------------------------------------------------------------------
# Assembly generators
# ---------------------------------------------------------------------------

def _make_inc(stride_bytes: int, n_reads: int) -> str:
    """
    Generate inline assembly for one ds_read_b32 throughput probe.

    Uses the exact timer sequence proven in timer_calibration.py:
      s_sendmsg_rtn_b64 + s_waitcnt lgkmcnt(0) for timestamps,
      s_sub_u32 / s_subb_u32 for 64-bit delta on the GPU,
      spill only the delta to v4:v5.

    Payload uses 16 rotating destination VGPRs (v10-v25) to avoid WAW
    scoreboard serialization.  A post-timing XOR anchor folds all 16
    registers into v0, keeping the compiler from eliminating the loads.

    Sequence
    --------
    1. Compute per-lane LDS address: lane_id * stride_bytes  → v2
    2. Initialise LDS: ds_write_b32 v2, 0xdeadbeef; wait
    3. Start timer  → s[8:9]; wait
    4. N × ds_read_b32 v{10 + i%16}, v2  (rotating, no WAW stalls)
    5. End timer    → s[10:11]; wait
    6. Anchor: XOR v10..v25 → v0 (outside timed region, defeats DCE)
    7. GPU-side 64-bit subtract: s[12:13] = s[10:11] - s[8:9]
    8. Spill delta to v4:v5, result to v1
    """
    assert stride_bytes in (4, 8, 16, 32, 64, 128), \
        f"stride must be power-of-2 in [4..128]: {stride_bytes}"
    assert n_reads >= 16, f"n_reads must be >= 16: {n_reads}"
    shift = stride_bytes.bit_length() - 1

    lines = [
        # --- compute per-lane byte address ---
        "v_mbcnt_lo_u32_b32 v2, -1, 0",          # v2 = lane_id (0..31)
        f"v_lshlrev_b32 v2, {shift}, v2",         # v2 = lane_id * stride_bytes

        # --- initialise LDS with known data ---
        "v_mov_b32 v3, 0xdeadbeef",
        "ds_write_b32 v2, v3",
        "s_waitcnt lgkmcnt(0)",

        # --- timed region (proven pattern from timer_calibration.py) ---
        "s_sendmsg_rtn_b64 s[8:9], sendmsg(MSG_RTN_GET_REALTIME)",
        "s_waitcnt lgkmcnt(0)",
    ]

    # --- N reads rotating through v10-v25 (no WAW hazards) ---
    for i in range(n_reads):
        dest = DEST_VGPRS[i % len(DEST_VGPRS)]
        lines.append(f"ds_read_b32 v{dest}, v2")

    lines += [
        # --- end timed region ---
        "s_sendmsg_rtn_b64 s[10:11], sendmsg(MSG_RTN_GET_REALTIME)",
        "s_waitcnt lgkmcnt(0)",

        # --- anchor phase: XOR all 16 dest VGPRs into v0 (outside timer) ---
        f"v_xor_b32 v0, v{DEST_VGPRS[0]}, v{DEST_VGPRS[1]}",
    ]
    for reg in DEST_VGPRS[2:]:
        lines.append(f"v_xor_b32 v0, v0, v{reg}")

    lines += [
        # --- GPU-side 64-bit subtraction: delta = end - start ---
        "s_sub_u32 s12, s10, s8",                 # delta_lo
        "s_subb_u32 s13, s11, s9",                # delta_hi (with borrow)

        # --- spill delta and read result to VGPRs ---
        "v_mov_b32 v4, s12",                      # delta[31:0]
        "v_mov_b32 v5, s13",                      # delta[63:32]
        "v_mov_b32 v1, v0",                        # anchor result (sanity)
    ]
    return "\n".join(f'"{line}\\n\\t"' for line in lines)


def _make_manifest(name: str, co_path: Path) -> dict:
    return {
        "name": name,
        "capture_prefix": "v",
        "initial_memory_hex": [],   # LDS does not use mem_buf
        "registers": {
            "vgprs": {"count": len(VGPR_INDICES), "indices": VGPR_INDICES},
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
# Build / run / parse
# ---------------------------------------------------------------------------

def _run(cmd: list[str], label: str) -> None:
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"ERROR: {label} failed\n{r.stderr.decode()}")


def _build(name: str, stride_bytes: int, n_reads: int) -> Path:
    """Compile the kernel for this (stride, n_reads) if not already cached."""
    co_path       = CO_DIR       / f"{name}.co"
    inc_path      = INC_DIR      / f"{name}.inc"
    dump_inc_path = DUMP_INC_DIR / f"{name}_dump.inc"
    manifest_path = MANIFEST_DIR / f"{name}.json"

    manifest = _make_manifest(name, co_path)

    if not co_path.exists():
        inc_path.write_text(_make_inc(stride_bytes, n_reads))
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

    return co_path


def _parse_output(name: str) -> dict[str, int]:
    """
    Parse the harness output file and return {regname: lane0_value}.
    File format: "v4: hex0 hex1 ... hex31" (one line per VGPR).
    """
    out_path = OUTPUTS_DIR / f"{name}_vector_registers"
    result: dict[str, int] = {}
    for line in out_path.read_text().splitlines():
        if ":" not in line:
            continue
        reg, rest = line.split(":", 1)
        reg = reg.strip()           # e.g. "v4"
        vals = rest.strip().split()
        if vals:
            result[reg] = int(vals[0], 16)  # lane 0 (uniform for spilled SGPRs)
    return result


def _measure(stride_bytes: int, n_reads: int, run_idx: int) -> int:
    """
    Run the kernel once and return the RTC tick delta.
    delta is the GPU-computed 64-bit subtract (v4:v5 = end - start).
    """
    name = f"ds_b32_s{stride_bytes:03d}_n{n_reads:05d}_r{run_idx:02d}"
    co_path = _build(name, stride_bytes, n_reads)

    manifest_path = MANIFEST_DIR / f"{name}.json"
    manifest = _make_manifest(name, co_path)
    manifest_path.write_text(json.dumps(manifest))

    _run([str(HARNESS_BIN), str(manifest_path)], f"harness {name}")

    regs = _parse_output(name)
    delta_lo = regs.get("v4", 0)
    delta_hi = regs.get("v5", 0)
    delta = (delta_hi << 32) | delta_lo
    return delta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not HARNESS_BIN.exists():
        sys.exit(f"ERROR: harness binary not found at {HARNESS_BIN}\n"
                 "       Build it first: cd bare_metal_test && make")

    for d in (INC_DIR, CO_DIR, DUMP_INC_DIR, MANIFEST_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  ds_read_b32 LDS bank-conflict latency sweep (GFX1101 / RDNA3)")
    print(f"  Strides: {STRIDES} bytes")
    print(f"  Slope method: N_LO={N_LO}, N_HI={N_HI} reads")
    print(f"  Runs per data point: {RUNS_PER_POINT}")
    print("=" * 72)

    results: list[tuple[int, int, float]] = []   # (stride, ways, ticks_per_read)

    for stride in STRIDES:
        ways = conflict_ways(stride)
        print(f"\n  stride={stride:3d} B  ({ways:2d}-way conflict)", flush=True)

        # --- Compile (one-time per stride/N pair) ---
        print(f"    compiling N={N_LO} ... ", end="", flush=True)
        _build(f"ds_b32_s{stride:03d}_n{N_LO:05d}_r00", stride, N_LO)
        print("OK")
        print(f"    compiling N={N_HI} ... ", end="", flush=True)
        _build(f"ds_b32_s{stride:03d}_n{N_HI:05d}_r00", stride, N_HI)
        print("OK")

        # --- Gather tick deltas at both data points ---
        deltas_lo: list[int] = []
        deltas_hi: list[int] = []

        for run in range(RUNS_PER_POINT):
            print(f"    run {run+1}/{RUNS_PER_POINT}:  ", end="", flush=True)
            d_lo = _measure(stride, N_LO, run)
            d_hi = _measure(stride, N_HI, run)
            deltas_lo.append(d_lo)
            deltas_hi.append(d_hi)
            print(f"N_LO={d_lo:>6}  N_HI={d_hi:>6}  Δ={d_hi - d_lo:>6}")

        med_lo = statistics.median(deltas_lo)
        med_hi = statistics.median(deltas_hi)
        ticks_per_read = (med_hi - med_lo) / (N_HI - N_LO)

        results.append((stride, ways, ticks_per_read))
        print(f"    → slope: ({med_hi:.0f} - {med_lo:.0f}) / {N_HI - N_LO}"
              f" = {ticks_per_read:.4f} ticks/read")

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    baseline = next((t for s, w, t in results if w == 1), None)

    print()
    print(f"{'stride':>8}  {'ways':>5}  {'ticks/read':>12}  {'penalty':>10}")
    print("-" * 45)
    for stride, ways, tpr in results:
        penalty = tpr - baseline if baseline is not None else 0.0
        print(f"{stride:>8}  {ways:>5}  {tpr:>12.4f}  {penalty:>+10.4f}")

    # -----------------------------------------------------------------------
    # Sail snippet
    # -----------------------------------------------------------------------
    if baseline is not None:
        print()
        print("─" * 72)
        print("  Paste into spec/execute/rdna3_ds_execute.sail")
        print("  (replace the let and the lds_penalty_cycles function):")
        print("─" * 72)

        # Convert ticks to GPU cycles: 1 RTC tick ≈ 25 GPU cycles (100MHz / 2.5GHz)
        # We'll report raw ticks and let the user calibrate.
        base_ticks = baseline
        print(f"\n// Measured via two-point slope: N_LO={N_LO}, N_HI={N_HI}")
        print(f"// Base (no-conflict) cost: {base_ticks:.4f} RTC ticks/read")
        print(f"let LDS_BASE_LATENCY_CYCLES : int = {max(1, round(base_ticks * 25))}"
              f"  // ≈ {base_ticks:.4f} × 25 GPU-cycles/tick")
        print()
        print("val lds_penalty_cycles : int -> int")
        print("function lds_penalty_cycles ways = {")

        way_to_penalty = {w: t - baseline for _, w, t in results}
        sorted_ways = sorted(way_to_penalty.keys())
        for i, w in enumerate(sorted_ways):
            penalty_ticks = way_to_penalty[w]
            penalty_cycles = max(0, round(penalty_ticks * 25))
            is_last = (i == len(sorted_ways) - 1)
            prefix = "    if" if i == 0 else "    else if"
            comment = f"  // +{penalty_ticks:.4f} ticks"
            print(f"{prefix} ways <= {w} then {{ {penalty_cycles} }}{comment}", end="")
            if is_last:
                print()
                print("    else { 0 }")
            else:
                print()
        print("}")


if __name__ == "__main__":
    main()

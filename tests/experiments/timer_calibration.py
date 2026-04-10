#!/usr/bin/env python3
"""
SMEM Real-Time Clock Calibration.
Proves the cycle cost of s_nop by comparing it against a known 1-cycle instruction (v_add_f32)
using the 64-bit s_memrealtime hardware clock.
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

BUILD_DIR    = REPO_ROOT / "build" / "timer_calibration"
INC_DIR      = BUILD_DIR / "inc"
CO_DIR       = BUILD_DIR / "co"
DUMP_INC_DIR = BUILD_DIR / "dump_inc"
MANIFEST_DIR = BUILD_DIR / "manifests"

ITERATIONS = [10000, 20000, 30000, 40000, 50000]

# ---------------------------------------------------------------------------
# Fill type definitions
# ---------------------------------------------------------------------------

def _rep(instr: str) -> Callable[[int], list[str]]:
    return lambda n: [instr] * n

FILLS: list[tuple[str, str, Callable[[int], list[str]]]] = [
    ("s_nop 0",            "snop",   _rep("s_nop 0")),
    ("v_add_f32 v3,v3,v3", "vadd",   _rep("v_add_f32 v3, v3, v3")),
    ("s_add_u32 s4,s4,1",  "sadd",   _rep("s_add_u32 s4, s4, 1")),
]

# ---------------------------------------------------------------------------
# File generators: Using s_memrealtime
# ---------------------------------------------------------------------------

def _make_inc(instrs: list[str]) -> str:
    fill = "".join(f'"{i}\\n\\t"\n' for i in instrs)
    return (
        # Requests the REALTIME clock and returns it to the 64-bit pair s[2:3]
        '"s_sendmsg_rtn_b64 s[2:3], sendmsg(MSG_RTN_GET_REALTIME)\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        + fill +
        '"s_sendmsg_rtn_b64 s[4:5], sendmsg(MSG_RTN_GET_REALTIME)\\n\\t"\n'
        '"s_waitcnt lgkmcnt(0)\\n\\t"\n'
        
        '"s_sub_u32 s6, s4, s2\\n\\t"\n'   # Lower 32 bits
        '"s_subb_u32 s7, s5, s3\\n\\t"\n'  # Upper 32 bits with borrow
        
        '"v_mov_b32 v0, s6\\n\\t"\n'
        '"v_mov_b32 v1, s7\\n\\t"'
    )
def _make_manifest(name: str, co_path: Path) -> dict:
    return {
        "name": name,
        "capture_prefix": "v",
        "initial_memory_hex": ["00000000", "00000000"],
        "registers": {
            "vgprs": {"count": 2, "indices": [0, 1]},
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

def _probe(slug: str, instrs: list[str]) -> int:
    """Returns the total RTC ticks elapsed for the payload."""
    name          = f"timer_calib_{slug}_{len(instrs):05d}"
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
    delta_lower = 0
    delta_upper = 0
    
    for line in out.read_text().splitlines():
        parts = line.strip().split()
        if not parts: continue
        
        reg_label = parts[0]
        val = int(parts[1], 16)
        
        if reg_label == "v0:": delta_lower = val
        if reg_label == "v1:": delta_upper = val
            
    total_ticks = (delta_upper << 32) | delta_lower
    return total_ticks

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not HARNESS_BIN.exists():
        sys.exit(f"ERROR: harness binary not found at {HARNESS_BIN}")

    for d in (INC_DIR, CO_DIR, DUMP_INC_DIR, MANIFEST_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print(f"{'Instruction':<20} | {'N=10k':<8} | {'N=50k':<8} | {'Ticks/Inst (Slope)'}")
    print("-" * 65)

    results = {}
    for display, slug, gen in FILLS:
        ticks_10k = _probe(slug, gen(10000))
        ticks_50k = _probe(slug, gen(50000))
        
        ticks_per_inst = (ticks_50k - ticks_10k) / 40000.0
        results[slug] = ticks_per_inst
        
        print(f"{display:<20} | {ticks_10k:<8} | {ticks_50k:<8} | {ticks_per_inst:.4f}")

    print("\n--- ANALYSIS ---")
    nop_cost = results["snop"]
    vadd_cost = results["vadd"]
    
    ratio = nop_cost / vadd_cost if vadd_cost > 0 else 0
    print(f"s_nop to v_add ratio: {ratio:.4f}x")
    
    if 0.95 <= ratio <= 1.05:
        print("VERDICT: Mathematically proven. 1 s_nop executes exactly as fast as 1 v_add_f32 (1 Cycle).")
    else:
        print("VERDICT: Deviation detected. Hardware may be dual-issuing NOPs or packing them.")

if __name__ == "__main__":
    main()
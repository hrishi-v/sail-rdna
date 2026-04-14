#!/usr/bin/env python3
"""Run a single test through both Sail and HIP, then print the register outputs side-by-side.

Usage:
    python3 show_test.py <test_name>
    python3 show_test.py s_load_no_wait
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MANIFEST_DIR  = REPO / "tests" / "manifests"
SETUP_DIR     = REPO / "tests" / "setups"
INC_DIR       = REPO / "bare_metal_test" / "asm"
BUILD_DIR     = REPO / "build" / "show_test"
SAIL_DUMP_DIR = REPO / "outputs" / "register_dumps"
HIP_OUT_DIR   = BUILD_DIR / "hip"
HARNESS_BIN   = REPO / "bare_metal_test" / "build" / "universal_harness"
INCLUDE_DIR   = REPO / "bare_metal_test" / "harness" / "include"
KERNEL_HIP    = REPO / "bare_metal_test" / "harness" / "kernel.hip"
EMU           = REPO / "rdna3_emu"
WAVE_SIZE     = 32


def run(cmd, label):
    r = subprocess.run(cmd, cwd=REPO)
    if r.returncode != 0:
        sys.exit(f"[FAIL] {label} (exit {r.returncode})")


def generate_setup(manifest):
    mem_hex  = manifest.get("initial_memory_hex", [])
    base_str = manifest.get("memory_base_addr")
    sgprs    = manifest.get("memory_sgprs")
    if not (mem_hex and base_str and sgprs):
        return
    base = int(base_str, 0)
    lines = [f"MEM32 {hex(base + i*4)} 0x{v}" for i, v in enumerate(mem_hex)]
    lines.append(f"SGPR {sgprs[0]} {hex(base & 0xFFFFFFFF)}")
    lines.append(f"SGPR {sgprs[1]} {hex((base >> 32) & 0xFFFFFFFF)}")
    SETUP_DIR.mkdir(exist_ok=True)
    (SETUP_DIR / f"{manifest['name']}.setup").write_text("\n".join(lines) + "\n")


def generate_dump_asm(manifest):
    lines = [
        "s_waitcnt vmcnt(0) lgkmcnt(0)",
        "s_waitcnt_vscnt null, 0",
        "s_mov_b32 exec_lo, -1",
        "v_mbcnt_lo_u32_b32 v30, -1, 0",
        "v_lshlrev_b32 v30, 2, v30",
    ]
    prefix = manifest.get("capture_prefix", "v")
    for i, idx in enumerate(manifest["registers"]["vgprs"]["indices"]):
        offset = i * 128
        src = f"v33" if prefix == "s" else f"v{idx}"
        if prefix == "s":
            lines.append(f"v_mov_b32 v33, s{idx}")
        lines.append(f"v_add_co_u32 v31, vcc_lo, {offset}, v30")
        lines.append(f"v_add_co_u32 v31, vcc_lo, s20, v31")
        lines.append(f"v_add_co_ci_u32_e64 v32, null, s21, 0, vcc_lo")
        lines.append(f"global_store_b32 v[31:32], {src}, off")
        lines.append("s_waitcnt_vscnt null, 0")
    return "\n".join(f'"{l}\\n\\t"' for l in lines)


def run_sail(test_name):
    print(f"\n[Sail] Assembling and running {test_name}...")
    run(["make", "assemble"], "make assemble")
    subprocess.run([str(EMU), f"tests/bin/{test_name}.bin"], cwd=REPO)


def run_hip(test_name, manifest):
    inc_file = INC_DIR / f"{test_name}.inc"
    if not inc_file.exists():
        sys.exit(f"[FAIL] No .inc file found: {inc_file}")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    HIP_OUT_DIR.mkdir(parents=True, exist_ok=True)

    dump_inc = BUILD_DIR / f"{test_name}_dump.inc"
    dump_inc.write_text(generate_dump_asm(manifest))

    co_path = HIP_OUT_DIR / f"{test_name}.co"
    print(f"\n[HIP] Compiling {test_name}.co...")
    run([
        "hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
        f"-I{INCLUDE_DIR.resolve()}",
        f'-DTEST_INC="{inc_file.resolve()}"',
        f'-DDUMP_INC="{dump_inc.resolve()}"',
        str(KERNEL_HIP), "-o", str(co_path),
    ], f"Compile {test_name}.co")

    run_manifest = BUILD_DIR / f"{test_name}_run.json"
    run_manifest.write_text(json.dumps({**manifest, "binary_path": str(co_path)}))

    print(f"[HIP] Running {test_name} on GPU...")
    run([str(HARNESS_BIN), str(run_manifest)], f"Run {test_name}")

    for f in (REPO / "outputs").glob(f"{test_name}_*registers"):
        shutil.move(str(f), str(HIP_OUT_DIR / f.name))


def parse_register_file(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        reg, _, vals = line.partition(":")
        result[reg.strip()] = [int(v, 16) for v in vals.split()]
    return result


def print_comparison(test_name, manifest):
    prefix   = manifest.get("capture_prefix", "v")
    indices  = manifest["registers"]["vgprs"]["indices"]

    sail_vec  = parse_register_file(SAIL_DUMP_DIR / f"vec_{test_name}.log")
    hip_file  = HIP_OUT_DIR / f"{test_name}_vector_registers"
    hip_regs  = parse_register_file(hip_file)

    print(f"\n{'='*60}")
    print(f"  Results: {test_name}")
    print(f"{'='*60}")
    print(f"  {'Register':<10}  {'Sail':>12}  {'HIP':>12}  {'Match'}")
    print(f"  {'-'*10}  {'-'*12}  {'-'*12}  {'-'*5}")

    for idx in indices:
        reg = f"{prefix}{idx}"
        sail_vals = sail_vec.get(reg, [])
        hip_vals  = hip_regs.get(reg, [])

        sail_display = hex(sail_vals[0]) if sail_vals else "?"
        hip_display  = hex(hip_vals[0])  if hip_vals  else "?"

        sail_set = set(sail_vals)
        hip_set  = set(hip_vals)
        match = "✓" if sail_set == hip_set else "✗ DIVERGE"

        print(f"  {reg:<10}  {sail_display:>12}  {hip_display:>12}  {match}")

        if sail_set != hip_set and len(sail_vals) == WAVE_SIZE:
            unique_sail = sorted(set(sail_vals))
            unique_hip  = sorted(set(hip_vals))
            if len(unique_sail) > 1 or len(unique_hip) > 1:
                print(f"    sail unique values: {[hex(v) for v in unique_sail]}")
                print(f"    hip  unique values: {[hex(v) for v in unique_hip]}")

    print()


def main():
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <test_name>")

    test_name = sys.argv[1]
    manifest_path = MANIFEST_DIR / f"{test_name}.json"
    if not manifest_path.exists():
        sys.exit(f"No manifest found: {manifest_path}")

    with open(manifest_path) as f:
        manifest = json.load(f)

    generate_setup(manifest)
    run_sail(test_name)
    run_hip(test_name, manifest)
    print_comparison(test_name, manifest)


if __name__ == "__main__":
    main()

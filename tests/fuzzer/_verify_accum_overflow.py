"""One-off: run accum_64/96 on bare metal + Sail, compare v1 sum per lane
to the mathematical expected value. Also recompile -O0/-O3 and grep for
vmcnt-drain patterns in the .s to see if the overflow survives opt level."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "diff"))
import parse  # noqa: E402

import importlib.util
sys.path.insert(0, str(REPO / "tests" / "experimental"))
_spec = importlib.util.spec_from_file_location(
    "exp_conftest", REPO / "tests" / "experimental" / "conftest.py")
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)
from elf_metadata import pattern_for  # noqa: E402


def expected_sum(N: int, j: int) -> int:
    # accum_N sums buffers b0..b_{N-1}. Their buffer_index in the kernarg
    # layout is 1..N (out is buffer_index 0). Each cell holds pattern_for(bi, j).
    total = 0
    for bi in range(1, N + 1):
        total = (total + pattern_for(bi, j)) & 0xFFFFFFFF
    return total


def _emit_asm_only(src: str, name: str, opt_level: str) -> Path:
    """Run only the first hipcc -S step to get the .s. Works for any -O."""
    exp.EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    hip_tmp = exp.EXP_BUILD_DIR / f"{name}_device.hip"
    hip_tmp.write_text(src)
    asm_path = exp.EXP_BUILD_DIR / f"{name}.s"
    subprocess.run(
        ["hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
         "-mcode-object-version=4", opt_level, "-S",
         str(hip_tmp), "-o", str(asm_path)],
        cwd=REPO, check=True, capture_output=True,
    )
    return asm_path


def run_one(name: str, N: int, opt_level: str = "-O1",
            asm_only: bool = False) -> dict:
    hip = REPO / "tests" / "fuzzer" / "generated" / f"{name}.hip"
    src = hip.read_text()
    kernel_name = exp._parse_kernel_name(src)
    instrumented = exp._inject_dump_hook(src)
    vgprs = exp._detect_vgprs(src)
    capture_prefix = exp._detect_capture_prefix(src)
    exp_name = f"_verify_{name}_{opt_level.strip('-')}"

    if asm_only:
        asm_file = _emit_asm_only(src, exp_name, opt_level)
        rows = []
    else:
        bin_src, elf = exp._compile_for_sail(
            instrumented, exp_name, kernel_name,
            vgpr_indices=vgprs, capture_prefix=capture_prefix,
            opt_level=opt_level,
        )
        manifest = exp._build_manifest(exp_name, kernel_name, src, elf)
        setup = exp._diff.SETUP_DIR / f"{exp_name}.setup"
        exp._write_setup_file(manifest, setup)
        sail_bin = REPO / "tests" / "bin" / f"{exp_name}.bin"
        shutil.copy(bin_src, sail_bin)

        emu = REPO / "rdna3_emu"
        subprocess.run([str(emu), str(sail_bin)], cwd=REPO,
                       capture_output=True, text=True, timeout=60)
        sail_vec = REPO / "outputs" / "register_dumps" / f"vec_{exp_name}.log"

        try:
            exp._run_hip_experimental(manifest, instrumented)
        except RuntimeError as e:
            return {"name": name, "opt": opt_level, "err": f"hip fail: {e}"}
        hip_vec = exp._diff.HIP_OUTPUT_DIR / f"{exp_name}_vector_registers"

        sail_d = parse.parse_register_file(sail_vec)
        hip_d = parse.parse_register_file(hip_vec)

        sail_v1 = sail_d.get("v1", [])
        hip_v1 = hip_d.get(f"{capture_prefix}1", [])

        rows = []
        for j in range(32):
            exp_val = expected_sum(N, j)
            s = sail_v1[j] if j < len(sail_v1) else None
            h = hip_v1[j] if j < len(hip_v1) else None
            rows.append((j, exp_val, s, h, s == exp_val, h == exp_val))

        asm_file = exp.EXP_BUILD_DIR / f"{exp_name}.s"
    asm_text = asm_file.read_text() if asm_file.exists() else ""
    # count global_load_b32 between BEGIN and END, and vmcnt waits in that window
    in_block = False
    loads = 0
    vmcnt_waits = 0
    for line in asm_text.splitlines():
        if "; BEGIN" in line:
            in_block = True
            continue
        if "; END" in line:
            in_block = False
            continue
        if in_block:
            t = line.strip()
            if t.startswith("global_load_b32"):
                loads += 1
            if t.startswith("s_waitcnt") and "vmcnt" in t:
                vmcnt_waits += 1

    return {
        "name": name, "opt": opt_level,
        "rows": rows, "asm_only": asm_only,
        "loads_in_block": loads, "vmcnt_waits_in_block": vmcnt_waits,
        "asm_file": str(asm_file),
    }


def report(res: dict) -> None:
    if "err" in res:
        print(f"=== {res['name']} {res['opt']}: ERROR {res['err']}")
        return
    print(f"\n=== {res['name']} {res['opt']} ===")
    print(f"  loads_in_BEGIN_END_block: {res['loads_in_block']}")
    print(f"  s_waitcnt vmcnt(..) in block: {res['vmcnt_waits_in_block']}")
    if res.get("asm_only"):
        print("  (asm-only: no bare metal run — link step unsupported at this opt)")
        return
    rows = res["rows"]
    mism_bm = [(j, e, s, h) for (j, e, s, h, ms, mb) in rows if not mb]
    mism_sail = [(j, e, s, h) for (j, e, s, h, ms, mb) in rows if not ms]
    print(f"  BARE METAL correct lanes: {32 - len(mism_bm)}/32")
    print(f"  SAIL       correct lanes: {32 - len(mism_sail)}/32")
    if mism_bm:
        print(f"  BARE-METAL MISMATCHES (first 8):")
        for j, e, s, h in mism_bm[:8]:
            print(f"    lane{j:02d}  expected=0x{e:08x}  bm=0x{(h or 0):08x}  sail=0x{(s or 0):08x}")
    else:
        print("  -> bare metal MATCHES expected for all 32 lanes.")
    if mism_sail:
        print(f"  (Sail mismatches first 4 lanes)")
        for j, e, s, h in mism_sail[:4]:
            print(f"    lane{j:02d}  expected=0x{e:08x}  sail=0x{(s or 0):08x}  bm=0x{(h or 0):08x}")


if __name__ == "__main__":
    targets = [("accum_64", 64), ("accum_96", 96)]
    # -O1: full Sail + bare metal. -O0/-O3: asm only (runtime linking fails
    # with standalone clang assembler due to HIP runtime function calls).
    for name, N in targets:
        report(run_one(name, N, "-O1", asm_only=False))
        report(run_one(name, N, "-O0", asm_only=True))
        report(run_one(name, N, "-O3", asm_only=True))

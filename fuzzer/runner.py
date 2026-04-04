from __future__ import annotations
import subprocess
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SAIL_EMU = _REPO_ROOT / "rdna3_emu"
_HIP_DIR = _REPO_ROOT / "bare_metal_test"

def assemble(asm: Path, elf: Path, raw: Path) -> None:
    """Sail needs the raw binary (.bin)."""
    subprocess.run([
        "clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1100",
        "-c", str(asm), "-o", str(elf)
    ], check=True, capture_output=True, text=True)
    subprocess.run([
        "llvm-objcopy", "-O", "binary", "-j", ".text", str(elf), str(raw)
    ], check=True, capture_output=True, text=True)

def run_sail(bin_path: Path) -> tuple[Path, Path]:
    """Runs the Sail emulator on the generated binary."""
    subprocess.run([str(_SAIL_EMU), str(bin_path)], cwd=_REPO_ROOT, check=True, capture_output=True, text=True)
    stem = bin_path.stem
    dump_dir = _REPO_ROOT / "outputs" / "register_dumps"
    return dump_dir / f"vec_{stem}.log", dump_dir / f"scal_{stem}.log"

def compile_and_run_hip(name: str, inc_path: Path, dump_inc_path: Path, build_dir: Path) -> Path:
    """Uses Universal Harness instead of compiling a new binary."""
    harness_bin = _HIP_DIR / "build" / "universal_harness"
    kernel_src  = _HIP_DIR / "harness" / "kernel.hip"
    include_dir = _HIP_DIR / "harness" / "include"
    co_path     = build_dir / f"{name}.co"
    manifest_path = _REPO_ROOT / "fuzzer" / "fuzz_tests" / f"{name}.json"

    subprocess.run([
        "hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
        f"-I{include_dir}", f'-DTEST_INC="{inc_path.resolve()}"', f'-DDUMP_INC="{dump_inc_path.resolve()}"',
        str(kernel_src), "-o", str(co_path)
    ], check=True, capture_output=True, text=True)

    manifest = {
        "name": name,
        "binary_path": str(co_path.resolve()),
        "registers": {
            "vgprs": { "count": 1, "indices": [0] },
            "sgprs": { "count": 0, "indices": [] }
        }
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    subprocess.run([str(harness_bin), str(manifest_path)], check=True, capture_output=True, text=True, cwd=_REPO_ROOT)
    return _REPO_ROOT / "outputs" / f"{name}_vector_registers"
from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SAIL_EMU = _REPO_ROOT / "rdna3_emu"
_HIP_DIR = _REPO_ROOT / "bare_metal_test"


def assemble(asm: Path, elf: Path, raw: Path) -> None:
    """Assemble an RDNA3 .asm file to a raw .bin via clang + llvm-objcopy."""
    subprocess.run(
        [
            "clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1100",
            "-c", str(asm), "-o", str(elf),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["llvm-objcopy", "-O", "binary", "-j", ".text", str(elf), str(raw)],
        check=True,
        capture_output=True,
        text=True,
    )

def run_sail(bin_path: Path) -> tuple[Path, Path]:
    """Run the Sail emulator on bin_path.
    """
    subprocess.run(
        [str(_SAIL_EMU), str(bin_path)],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stem = bin_path.stem
    dump_dir = _REPO_ROOT / "outputs" / "register_dumps"
    return dump_dir / f"vec_{stem}.log", dump_dir / f"scal_{stem}.log"


def compile_and_run_hip(
    name: str,
    inc_path: Path,
    dump_inc_path: Path,
    build_dir: Path,
) -> Path:
    """Compile and run a single HIP fuzz test.
    """
    harness_srcs = [
        str(_HIP_DIR / "harness" / "src" / "harness.cpp"),
        str(_HIP_DIR / "harness" / "kernel.hip"),
    ]
    binary = build_dir / name

    subprocess.run(
        [
            "hipcc", "-O0", "-g",
            f"-I{_HIP_DIR / 'harness' / 'include'}",
            f'-DTEST_INC="{inc_path.resolve()}"',
            f'-DDUMP_INC="{dump_inc_path.resolve()}"',
            "-DNUM_VGPRS=1",
            "-DNUM_SGPRS=0",
            "-DVGPR_INDICES={0}",
            "-DSGPR_INDICES={}",
            '-DCAPTURE_PREFIX="v"',
            f'-DTEST_NAME="{name}"',
            *harness_srcs,
            "-o", str(binary),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=_HIP_DIR,
    )

    subprocess.run(
        [str(binary.resolve())],
        check=True,
        capture_output=True,
        text=True,
        cwd=_HIP_DIR,
    )
    return _HIP_DIR / "outputs" / f"{name}_vector_registers"

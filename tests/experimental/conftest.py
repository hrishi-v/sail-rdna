from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = REPO_ROOT / "tests" / "experimental"
EXP_BUILD_DIR = REPO_ROOT / "build" / "experimental"

_DIFF_CONFTEST_PATH = REPO_ROOT / "tests" / "diff" / "conftest.py"
_spec = importlib.util.spec_from_file_location("_diff_conftest_helpers", _DIFF_CONFTEST_PATH)
_diff = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(REPO_ROOT / "tests" / "diff"))
_spec.loader.exec_module(_diff)

import parse  # noqa: E402  (tests/diff/parse.py, now on sys.path)


# ---------------------------------------------------------------------------
# Kernel source parsing heuristics
# ---------------------------------------------------------------------------

_KERNEL_RE = re.compile(r'__global__\s+\w[\w\s\*&]*\s+(\w+)\s*\(')
_VGPR_RE = re.compile(r'\bv(\d+)\b')


def _parse_kernel_name(src: str) -> str | None:
    m = _KERNEL_RE.search(src)
    return m.group(1) if m else None


def _extract_asm_blocks(src: str) -> list[str]:
    blocks: list[str] = []
    for keyword in ("__asm__", "asm"):
        for m in re.finditer(rf'\b{keyword}\s+volatile\s*\(', src):
            start = m.end()
            depth = 1
            i = start
            while i < len(src) and depth:
                if src[i] == '(':
                    depth += 1
                elif src[i] == ')':
                    depth -= 1
                i += 1
            blocks.append(src[start:i - 1])
    return blocks


def _detect_vgprs(src: str) -> list[int]:
    vgprs: set[int] = set()
    for block in _extract_asm_blocks(src):
        for m in _VGPR_RE.finditer(block):
            idx = int(m.group(1))
            if idx < 64:  # skip scratch regs used by dump logic (v30-v33)
                vgprs.add(idx)
    for high in (30, 31, 32, 33):
        vgprs.discard(high)
    if vgprs:
        return sorted(vgprs)[:8]
    return [0, 1, 2, 3]


def _uses_tid(src: str) -> bool:
    return 'threadIdx' in src or re.search(r'\btid\b', src) is not None


def _detect_capture_prefix(src: str) -> str:
    """Return 's' if asm writes to scalar regs; else 'v'."""
    for block in _extract_asm_blocks(src):
        if re.search(r's_mov_b32\s+s\d+', block) or re.search(r'"=s"', block):
            return "s"
    return "v"


# ---------------------------------------------------------------------------
# Manifest + setup generation
# ---------------------------------------------------------------------------

DEFAULT_MEM_BASE = 0x2000
DEFAULT_MEM_VALUES = [
    "cafef00d", "deadbeef", "12345678", "87654321",
    "00000001", "00000002", "00000003", "00000004",
]
DEFAULT_MEM_SGPRS = [0, 1]


def _build_manifest(name: str, kernel_name: str, src: str) -> dict:
    vgprs = _detect_vgprs(src)
    capture_prefix = _detect_capture_prefix(src)
    manifest = {
        "name": name,
        "kernel_name": kernel_name,
        "capture_prefix": capture_prefix,
        "binary_path": f"tests/bin/{name}.bin",
        "initial_memory_hex": list(DEFAULT_MEM_VALUES),
        "memory_base_addr": hex(DEFAULT_MEM_BASE),
        "memory_sgprs": list(DEFAULT_MEM_SGPRS),
        "registers": {
            "vgprs": {"count": len(vgprs), "indices": vgprs},
            "sgprs": {"count": 0, "indices": []},
        },
    }
    if _uses_tid(src):
        manifest["vgpr_lane_ids"] = [0]
    else:
        manifest["vgpr_lane_ids"] = []
    return manifest


def _write_setup_file(manifest: dict, path: Path) -> None:
    base = int(manifest["memory_base_addr"], 0)
    lines = [f"MEM32 {hex(base + i * 4)} 0x{v}"
             for i, v in enumerate(manifest["initial_memory_hex"])]
    lo, hi = manifest["memory_sgprs"]
    lines.append(f"SGPR {lo} {hex(base & 0xFFFFFFFF)}")
    lines.append(f"SGPR {hi} {hex((base >> 32) & 0xFFFFFFFF)}")
    for vidx in manifest.get("vgpr_lane_ids", []):
        lines.append(f"VGPR_LANE_ID {vidx}")
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Kernel instrumentation
# ---------------------------------------------------------------------------

_DUMP_HOOK_PLACEHOLDER = 'asm volatile("// DUMP_HOOK");'


def _inject_dump_hook(src: str) -> str:
    """Insert DUMP_HOOK placeholder at the end of the first __global__ body."""
    if 'DUMP_HOOK' in src:
        return src
    m = re.search(r'__global__[^{]*\{', src)
    if not m:
        return src
    start = m.end()
    depth = 1
    i = start
    while i < len(src) and depth > 0:
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
        i += 1
    close_idx = i - 1
    hook = f'\n    {_DUMP_HOOK_PLACEHOLDER}\n'
    return src[:close_idx] + hook + src[close_idx:]


# ---------------------------------------------------------------------------
# Sail compilation (.hip -> .co -> .bin) and execution
# ---------------------------------------------------------------------------

def _compile_for_sail(instrumented_src: str, manifest: dict, name: str) -> Path:
    EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    dump_asm = _diff._generate_dump_logic(manifest)
    device_src = instrumented_src.replace(
        _DUMP_HOOK_PLACEHOLDER,
        f"asm volatile(\n{dump_asm}\n);",
    )
    hip_tmp = EXP_BUILD_DIR / f"{name}_device.hip"
    hip_tmp.write_text(device_src)
    co_path = EXP_BUILD_DIR / f"{name}.co"
    bin_path = EXP_BUILD_DIR / f"{name}.bin"
    _diff._run(
        ["hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
         str(hip_tmp), "-o", str(co_path)],
        REPO_ROOT, f"hipcc {name} (device-only)",
    )
    _diff._run(
        ["llvm-objcopy", "-O", "binary", "-j", ".text",
         str(co_path), str(bin_path)],
        REPO_ROOT, f"llvm-objcopy {name}.bin",
    )
    return bin_path


def _run_sail_single(bin_path: Path) -> None:
    emu = REPO_ROOT / "rdna3_emu"
    if not emu.exists():
        _diff._run(["make", "emu"], REPO_ROOT, "build rdna3_emu")
    _diff._run([str(emu), str(bin_path)], REPO_ROOT, f"sail run {bin_path.name}")


# ---------------------------------------------------------------------------
# Comparison report
# ---------------------------------------------------------------------------

def _format_manifest_summary(manifest: dict) -> list[str]:
    vgpr_idx = manifest["registers"]["vgprs"]["indices"]
    return [
        f"  kernel_name     : {manifest['kernel_name']}",
        f"  capture_prefix  : {manifest['capture_prefix']}",
        f"  capture vgprs   : {vgpr_idx}",
        f"  memory_base     : {manifest['memory_base_addr']}",
        f"  memory_sgprs    : {manifest['memory_sgprs']}",
        f"  vgpr_lane_ids   : {manifest.get('vgpr_lane_ids', [])}",
        f"  initial_mem[0:4]: {manifest['initial_memory_hex'][:4]}",
    ]


def _format_register_dump(prefix: str, dump: dict, indices: list[int]) -> list[str]:
    out = []
    for idx in indices:
        key = f"{prefix}{idx}"
        vals = dump.get(key, dump.get(f"v{idx}"))
        if vals is None:
            out.append(f"  {key}: <missing>")
            continue
        lanes = " ".join(f"{v:08x}" for v in vals[:8])
        suffix = " ..." if len(vals) > 8 else ""
        out.append(f"  {key}: {lanes}{suffix}")
    return out


def _compare_dumps(manifest: dict, sail_vec: Path, hip_vec: Path) -> tuple[list[str], list[str], bool]:
    """Returns (detail_lines, per_register_status, all_ok)."""
    if not sail_vec.exists():
        return ([f"Sail dump missing: {sail_vec}"], [], False)
    if not hip_vec.exists():
        return ([f"HIP dump missing: {hip_vec}"], [], False)

    sail_dump = parse.parse_register_file(sail_vec)
    hip_dump = parse.parse_register_file(hip_vec)

    capture = manifest["capture_prefix"]
    indices = manifest["registers"]["vgprs"]["indices"]

    details: list[str] = []
    status: list[str] = []
    all_ok = True
    for idx in indices:
        reg_hip = f"{capture}{idx}"
        # Sail always dumps vector regs under "vN" in vec_*.log, but when
        # capture_prefix=="s" the instrumentation wrote an SGPR into a VGPR
        # for output -- compare HIP's sN column against Sail's vN column.
        sail_key = f"v{idx}"
        sail_vals = sail_dump.get(sail_key)
        hip_vals = hip_dump.get(reg_hip)
        if sail_vals is None or hip_vals is None:
            status.append(f"{reg_hip}: MISSING (sail={sail_vals is not None}, hip={hip_vals is not None})")
            all_ok = False
            continue
        mismatches = [(l, s, h) for l, (s, h) in enumerate(zip(sail_vals, hip_vals)) if s != h]
        if not mismatches:
            status.append(f"{reg_hip}: MATCH (32/32 lanes)")
        else:
            all_ok = False
            status.append(
                f"{reg_hip}: MISMATCH ({len(mismatches)}/{len(sail_vals)} lanes differ)"
            )
            for l, s, h in mismatches[:4]:
                details.append(f"    {reg_hip} lane{l:02d}: sail=0x{s:08x}  hip=0x{h:08x}")
            if len(mismatches) > 4:
                details.append(f"    ... (+{len(mismatches) - 4} more lanes)")
    return (details, status, all_ok)


# ---------------------------------------------------------------------------
# Pytest integration
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--experimental",
        action="store_true",
        default=False,
        help="Run the experimental auto-kernel pipeline across tests/experimental/*.hip.",
    )
    parser.addoption(
        "--kernel",
        action="store",
        default=None,
        metavar="PATH",
        help="Run the experimental auto-kernel pipeline on a single .hip file.",
    )


def _collect_hip_files(config: pytest.Config) -> list[Path]:
    single = config.getoption("--kernel", default=None)
    if single:
        p = Path(single).expanduser().resolve()
        if not p.exists():
            raise pytest.UsageError(f"--kernel path not found: {p}")
        return [p]
    if config.getoption("--experimental", default=False):
        return sorted(EXP_DIR.glob("*.hip"))
    return []


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "hip_kernel_path" not in metafunc.fixturenames:
        return
    hips = _collect_hip_files(metafunc.config)
    metafunc.parametrize("hip_kernel_path", hips, ids=[p.stem for p in hips])


@pytest.fixture(scope="session")
def experimental_env() -> None:
    EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    _diff.SETUP_DIR.mkdir(parents=True, exist_ok=True)
    _diff.HIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    emu = REPO_ROOT / "rdna3_emu"
    if not emu.exists():
        _diff._run(["make", "emu"], REPO_ROOT, "build rdna3_emu")


# Expose helpers + paths to the test module.
__all__ = [
    "REPO_ROOT", "EXP_DIR", "EXP_BUILD_DIR",
    "_diff", "parse",
    "_parse_kernel_name", "_build_manifest", "_write_setup_file",
    "_inject_dump_hook", "_compile_for_sail", "_run_sail_single",
    "_format_manifest_summary", "_format_register_dump", "_compare_dumps",
    "_DUMP_HOOK_PLACEHOLDER",
]

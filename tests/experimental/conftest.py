from __future__ import annotations

import importlib.util
import re
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

sys.path.insert(0, str(EXP_DIR))
from elf_metadata import (  # noqa: E402
    DATA_BUFFER_BASE,
    DATA_BUFFER_STRIDE,
    KERNARG_BASE,
    WORDS_PER_BUFFER,
    parse_kernel_args,
    pattern_for,
)


WAVE_SIZE = 32


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
            if idx < 64:
                vgprs.add(idx)
    for high in (30, 31, 32, 33):
        vgprs.discard(high)
    if vgprs:
        return sorted(vgprs)[:8]
    return [0, 1, 2, 3]


def _uses_tid(src: str) -> bool:
    return 'threadIdx' in src or re.search(r'\btid\b', src) is not None


def _detect_capture_prefix(src: str) -> str:
    for block in _extract_asm_blocks(src):
        if re.search(r's_mov_b32\s+s\d+', block) or re.search(r'"=s"', block):
            return "s"
    return "v"


# ---------------------------------------------------------------------------
# Manifest construction (metadata-driven)
# ---------------------------------------------------------------------------


def _assign_kernarg_layout(args: list[dict]) -> list[dict]:
    """Return a copy of args with `buffer_index` + `buffer_addr` added for
    every `global_buffer` entry (in source order)."""
    result = []
    next_buf = 0
    for a in args:
        entry = dict(a)
        if a["value_kind"] == "global_buffer":
            entry["buffer_index"] = next_buf
            entry["buffer_addr"] = DATA_BUFFER_BASE + next_buf * DATA_BUFFER_STRIDE
            next_buf += 1
        result.append(entry)
    return result


def _build_manifest(name: str, kernel_name: str, src: str, elf_path: Path) -> dict:
    vgprs = _detect_vgprs(src)
    capture_prefix = _detect_capture_prefix(src)
    raw_args = parse_kernel_args(elf_path, kernel_name)
    kernarg_args = _assign_kernarg_layout(raw_args)
    manifest = {
        "name": name,
        "kernel_name": kernel_name,
        "capture_prefix": capture_prefix,
        "binary_path": f"tests/bin/{name}.bin",
        "registers": {
            "vgprs": {"count": len(vgprs), "indices": vgprs},
            "sgprs": {"count": 0, "indices": []},
        },
        "kernarg_base": KERNARG_BASE,
        "kernarg_args": kernarg_args,
        "data_buffer_words": WORDS_PER_BUFFER,
        "vgpr_lane_ids": [0] if _uses_tid(src) else [],
    }
    return manifest


def _write_setup_file(manifest: dict, path: Path) -> None:
    lines: list[str] = []
    kernarg_base = manifest["kernarg_base"]

    for arg in manifest["kernarg_args"]:
        off = arg["offset"]
        vk = arg["value_kind"]
        if vk == "global_buffer":
            buf_addr = arg["buffer_addr"]
            lines.append(f"MEM32 {hex(kernarg_base + off)} {hex(buf_addr & 0xFFFFFFFF)}")
            lines.append(f"MEM32 {hex(kernarg_base + off + 4)} {hex((buf_addr >> 32) & 0xFFFFFFFF)}")
            for j in range(manifest["data_buffer_words"]):
                lines.append(f"MEM32 {hex(buf_addr + j * 4)} {hex(pattern_for(arg['buffer_index'], j))}")
        elif vk == "by_value":
            for w in range(0, arg["size"], 4):
                lines.append(f"MEM32 {hex(kernarg_base + off + w)} 0x0")
        else:
            raise RuntimeError(f"Unsupported value_kind in setup: {vk}")

    lo = kernarg_base & 0xFFFFFFFF
    hi = (kernarg_base >> 32) & 0xFFFFFFFF
    lines.append(f"SGPR 0 {hex(lo)}")
    lines.append(f"SGPR 1 {hex(hi)}")
    lines.append(f"SGPR 2 {hex(lo)}")
    lines.append(f"SGPR 3 {hex(hi)}")

    for vidx in manifest.get("vgpr_lane_ids", []):
        lines.append(f"VGPR_LANE_ID {vidx}")

    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Kernel instrumentation
# ---------------------------------------------------------------------------

_DUMP_HOOK_PLACEHOLDER = 'asm volatile("// DUMP_HOOK");'


def _build_dump_hook_block(kernel_src: str, kernel_name: str,
                           vgpr_indices: list[int], capture_prefix: str) -> str:
    """C++ block that initialises s20:s21 from the kernel's first pointer
    param and runs the dump asm. Used verbatim by both the Sail compile and
    the HIP wrapper so register allocation is identical in both compiles."""
    first_ptr = _first_pointer_param(kernel_src, kernel_name)
    fragment_manifest = {
        "capture_prefix": capture_prefix,
        "registers": {"vgprs": {"indices": vgpr_indices}},
    }
    dump_asm = _diff._generate_dump_logic(fragment_manifest)
    return (
        "{\n"
        f"    unsigned int _dump_lo = (unsigned int)((unsigned long long){first_ptr} & 0xFFFFFFFFULL);\n"
        f"    unsigned int _dump_hi = (unsigned int)((unsigned long long){first_ptr} >> 32);\n"
        "    asm volatile(\n"
        '        "s_mov_b32 s20, %0\\n\\t"\n'
        '        "s_mov_b32 s21, %1\\n\\t"\n'
        f"{dump_asm}\n"
        "        :\n"
        '        : "s"(_dump_lo), "s"(_dump_hi)\n'
        '        : "v30", "v31", "v32", "v33",\n'
        '          "s20", "s21", "vcc", "exec", "memory"\n'
        "    );\n"
        "}\n"
    )


def _first_pointer_param(kernel_src: str, kernel_name: str) -> str:
    m = re.search(rf'{re.escape(kernel_name)}\s*\(([^)]*)\)', kernel_src)
    if not m:
        raise RuntimeError(f"Could not find signature of kernel {kernel_name}")
    ptr_match = re.search(r'\*\s*(\w+)', m.group(1))
    if not ptr_match:
        raise RuntimeError(f"Kernel {kernel_name} has no pointer parameter")
    return ptr_match.group(1)


def _inject_dump_hook(src: str) -> str:
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

def _compile_for_sail(
    instrumented_src: str, name: str, kernel_name: str,
    vgpr_indices: list[int], capture_prefix: str,
    opt_level: str = "-O1",
) -> tuple[Path, Path]:
    EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    dump_block = _build_dump_hook_block(
        instrumented_src, kernel_name, vgpr_indices, capture_prefix,
    )
    device_src = instrumented_src.replace(_DUMP_HOOK_PLACEHOLDER, dump_block)
    hip_tmp = EXP_BUILD_DIR / f"{name}_device.hip"
    hip_tmp.write_text(device_src)
    asm_path = EXP_BUILD_DIR / f"{name}.s"
    elf_path = EXP_BUILD_DIR / f"{name}.elf"
    bin_path = EXP_BUILD_DIR / f"{name}.bin"
    _diff._run(
        ["hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
         "-mcode-object-version=4", opt_level, "-S",
         str(hip_tmp), "-o", str(asm_path)],
        REPO_ROOT, f"hipcc {name} (emit asm)",
    )
    _diff._run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         "-c", str(asm_path), "-o", str(elf_path)],
        REPO_ROOT, f"clang assemble {name}.elf",
    )
    _diff._run(
        ["llvm-objcopy", "-O", "binary", "-j", ".text",
         str(elf_path), str(bin_path)],
        REPO_ROOT, f"llvm-objcopy {name}.bin",
    )
    return bin_path, elf_path


def _run_sail_single(bin_path: Path) -> None:
    emu = REPO_ROOT / "rdna3_emu"
    if not emu.exists():
        _diff._run(["make", "emu"], REPO_ROOT, "build rdna3_emu")
    _diff._run([str(emu), str(bin_path)], REPO_ROOT, f"sail run {bin_path.name}")


# ---------------------------------------------------------------------------
# HIP wrapper generation (metadata-driven)
# ---------------------------------------------------------------------------

def _generate_hip_wrapper(manifest: dict, kernel_src: str) -> str:
    kernel_name = manifest["kernel_name"]
    vgpr_indices = manifest["registers"]["vgprs"]["indices"]
    vgpr_count = len(vgpr_indices)
    buf_words = max(manifest["data_buffer_words"], vgpr_count * WAVE_SIZE)
    kernarg_args = manifest["kernarg_args"]

    globals_bufs = [a for a in kernarg_args if a["value_kind"] == "global_buffer"]
    if not globals_bufs:
        raise RuntimeError("Kernel has no global_buffer args; cannot set dump target")

    first_gb = globals_bufs[0]

    dump_block = _build_dump_hook_block(
        kernel_src, kernel_name, vgpr_indices, manifest["capture_prefix"],
    )
    instrumented_kernel = kernel_src.replace(_DUMP_HOOK_PLACEHOLDER, dump_block)

    alloc_lines: list[str] = []
    call_args: list[str] = []
    for i, a in enumerate(kernarg_args):
        if a["value_kind"] == "global_buffer":
            bi = a["buffer_index"]
            alloc_lines.append(f"    int* d_buf_{bi} = nullptr;")
            alloc_lines.append(f"    hipMalloc(&d_buf_{bi}, BUF_BYTES);")
            alloc_lines.append(f"    std::vector<int> h_buf_{bi}(BUF_WORDS);")
            alloc_lines.append(
                f"    for (int j = 0; j < {WORDS_PER_BUFFER}; j++) "
                f"h_buf_{bi}[j] = static_cast<int>(0xDEAD0000u + ({bi} << 5) + j);"
            )
            alloc_lines.append(
                f"    hipMemcpy(d_buf_{bi}, h_buf_{bi}.data(), BUF_BYTES, hipMemcpyHostToDevice);"
            )
            call_args.append(f"d_buf_{bi}")
        else:  # by_value
            alloc_lines.append(f"    int arg_{i}_byvalue = 0;")
            call_args.append(f"arg_{i}_byvalue")

    free_lines = "\n".join(
        f"    hipFree(d_buf_{a['buffer_index']});"
        for a in globals_bufs
    )

    write_lines: list[str] = []
    for i, reg_idx in enumerate(vgpr_indices):
        write_lines.append(f'    out << "{manifest["capture_prefix"]}{reg_idx}:";')
        write_lines.append(f"    for (int lane = 0; lane < {WAVE_SIZE}; lane++)")
        write_lines.append(
            f'        out << " " << std::hex << std::setfill(\'0\')'
            f' << std::setw(8) << static_cast<unsigned>(h_dump[{i} * {WAVE_SIZE} + lane]);'
        )
        write_lines.append('    out << "\\n";')

    out_file = _diff.HIP_OUTPUT_DIR / f"{manifest['name']}_vector_registers"
    dump_buf_index = first_gb["buffer_index"]

    wrapper = f"""\
#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <hip/hip_runtime.h>

{instrumented_kernel}

int main() {{
    constexpr int BUF_WORDS = {buf_words};
    constexpr size_t BUF_BYTES = BUF_WORDS * sizeof(int);

{chr(10).join(alloc_lines)}

    {kernel_name}<<<1, {WAVE_SIZE}>>>({", ".join(call_args)});
    hipDeviceSynchronize();

    std::vector<int> h_dump({vgpr_count} * {WAVE_SIZE});
    hipMemcpy(h_dump.data(), d_buf_{dump_buf_index},
              h_dump.size() * sizeof(int), hipMemcpyDeviceToHost);

    std::ofstream out("{out_file}");
{chr(10).join(write_lines)}

{free_lines}
    return 0;
}}
"""
    return wrapper


def _run_hip_experimental(manifest: dict, kernel_src: str) -> None:
    EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    _diff.HIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    wrapper = _generate_hip_wrapper(manifest, kernel_src)
    wrapper_path = EXP_BUILD_DIR / f"{manifest['name']}_wrapper.hip"
    wrapper_path.write_text(wrapper)

    exe = EXP_BUILD_DIR / f"{manifest['name']}_wrapper.out"
    _diff._run(
        ["hipcc", "--offload-arch=gfx1101", "-mcode-object-version=4",
         "-O1", str(wrapper_path), "-o", str(exe)],
        REPO_ROOT, f"hipcc experimental wrapper {manifest['name']}",
    )
    _diff._run([str(exe)], REPO_ROOT, f"run experimental wrapper {manifest['name']}")


# ---------------------------------------------------------------------------
# Comparison report
# ---------------------------------------------------------------------------

def _format_manifest_summary(manifest: dict) -> list[str]:
    vgpr_idx = manifest["registers"]["vgprs"]["indices"]
    arg_summary = ", ".join(
        f"{a['value_kind']}@0x{a['offset']:x}" + (
            f"->{hex(a['buffer_addr'])}" if a["value_kind"] == "global_buffer" else ""
        )
        for a in manifest["kernarg_args"]
    )
    return [
        f"  kernel_name     : {manifest['kernel_name']}",
        f"  capture_prefix  : {manifest['capture_prefix']}",
        f"  capture vgprs   : {vgpr_idx}",
        f"  kernarg_base    : {hex(manifest['kernarg_base'])}",
        f"  kernarg_args    : {arg_summary}",
        f"  vgpr_lane_ids   : {manifest.get('vgpr_lane_ids', [])}",
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


__all__ = [
    "REPO_ROOT", "EXP_DIR", "EXP_BUILD_DIR",
    "_diff", "parse",
    "_parse_kernel_name", "_build_manifest", "_write_setup_file",
    "_inject_dump_hook", "_compile_for_sail", "_run_sail_single",
    "_run_hip_experimental",
    "_format_manifest_summary", "_format_register_dump", "_compare_dumps",
    "_DUMP_HOOK_PLACEHOLDER",
]

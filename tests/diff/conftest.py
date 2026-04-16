from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import parse
from parse import RegisterDump

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SAIL_DUMP_DIR = REPO_ROOT / "outputs" / "register_dumps"
HIP_OUTPUT_DIR = REPO_ROOT / "build" / "hip"
HIP_BF_OUTPUT_DIR = REPO_ROOT / "build" / "hip_brute_force"
MANIFEST_DIR = REPO_ROOT / "tests" / "manifests"
KERNEL_DIR = REPO_ROOT / "tests" / "kernels"
INC_DIR = REPO_ROOT / "bare_metal_test" / "asm"
PYTEST_BUILD_DIR = REPO_ROOT / "build" / "pytest"

WAVE_SIZE = 32
SETUP_DIR = REPO_ROOT / "tests" / "setups"

# ---------------------------------------------------------------------------
# Sentinel register allow-lists
# ---------------------------------------------------------------------------

_SAIL_ALLOWED_NONZERO: dict[str, frozenset[str]] = {
    "add_one":         frozenset({"v5"}),
    "v_add":           frozenset({"v0", "v1"}),
    "scalar_alu":      frozenset({"s0", "s1", "s2"}),
    "vector_alu":      frozenset({"v0", "v1", "s0"}),
    "imm_pc":          frozenset({"v1", "v2"}),
    "flat_store":      frozenset({"v0", "v1", "v2", "v3"}),
    "s_load_b64_test": frozenset({"v0", "v1", "v2", "v3", "s0", "s1", "s2", "s3"}),
    "s_branch":        frozenset({"v0"}),
    "flat_b64_test":   frozenset({"v0", "v1", "v2", "v3", "v4", "v5"}),
    "v_mad_u64_test":       frozenset({"v0", "v1", "v2", "v3", "s0", "s1"}),
    "v_ashrrev_i32_test":  frozenset({"v0"}),
    "v_add_co_ci_u32_test": frozenset({"v1", "s10", "s106"}),
    "v_add_co_u32_test":   frozenset({"v0", "v1", "s10", "s106"}),
    "v_lshlrev_b64_test":  frozenset({"v0", "v1", "v2"}),
    "global_load_store_test": frozenset({"v0", "v1", "v2"}),
    "s_and_b32_test": frozenset({"s0", "s1", "s2"}),
    "s_load_b32_test": frozenset({"s0", "s2", "v0", "v2"}),
    "vmcnt_stale_read": frozenset({"v0", "v2", "v3", "v4"}),
    "vscnt_endpgm":    frozenset({"v0", "v2"}),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path, label: str) -> None:
    """Run a shell command, streaming its output live.  Raises on failure."""
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")


def _generate_dump_logic(manifest):
    """Generate RDNA3 assembly (as C-string lines) that dumps registers to
    the vgpr_out buffer (s20:s21).  When capture_prefix is "s", indices
    refer to SGPRs and are broadcast to a VGPR before storing."""
    lines = [
        "s_waitcnt vmcnt(0) lgkmcnt(0)",
        "s_waitcnt_vscnt null, 0",
        "s_mov_b32 exec_lo, -1",
        "v_mbcnt_lo_u32_b32 v30, -1, 0",
        "v_lshlrev_b32 v30, 2, v30",
    ]

    capture_prefix = manifest.get("capture_prefix", "v")

    for i, reg_idx in enumerate(manifest["registers"]["vgprs"]["indices"]):
        reg_block_offset = i * 128

        if capture_prefix == "s":
            lines.append(f"v_mov_b32 v33, s{reg_idx}")
            src_reg = "v33"
        else:
            src_reg = f"v{reg_idx}"

        lines.append(f"v_add_co_u32 v31, vcc_lo, {reg_block_offset}, v30")
        lines.append(f"v_add_co_u32 v31, vcc_lo, s20, v31")
        lines.append(f"v_add_co_ci_u32_e64 v32, null, s21, 0, vcc_lo")
        lines.append(f"global_store_b32 v[31:32], {src_reg}, off")
        lines.append("s_waitcnt_vscnt null, 0")

    c_string_lines = [f'"{line}\\n\\t"' for line in lines]
    return "\n".join(c_string_lines)


# ---------------------------------------------------------------------------
# Setup file generation
# ---------------------------------------------------------------------------


def _generate_setup_files() -> None:
    """Emit tests/setups/<name>.setup for any manifest that specifies
    initial_memory_hex + memory_base_addr + memory_sgprs.  These files are
    picked up by the Sail run_test harness to pre-load memory and pointer
    registers before execution."""
    SETUP_DIR.mkdir(exist_ok=True)
    for manifest_path in MANIFEST_DIR.glob("*.json"):
        with open(manifest_path) as f:
            manifest = json.load(f)

        mem_hex   = manifest.get("initial_memory_hex", [])
        base_str  = manifest.get("memory_base_addr")
        sgprs     = manifest.get("memory_sgprs")

        if not (mem_hex and base_str and sgprs):
            continue

        base_addr = int(base_str, 0)
        lines: list[str] = []

        for i, val in enumerate(mem_hex):
            lines.append(f"MEM32 {hex(base_addr + i * 4)} 0x{val}")

        # Write the 64-bit pointer into the SGPR pair.
        lines.append(f"SGPR {sgprs[0]} {hex(base_addr & 0xFFFFFFFF)}")
        lines.append(f"SGPR {sgprs[1]} {hex((base_addr >> 32) & 0xFFFFFFFF)}")

        # Optionally initialise VGPRs with lane IDs (e.g. for tid).
        for vgpr_idx in manifest.get("vgpr_lane_ids", []):
            lines.append(f"VGPR_LANE_ID {vgpr_idx}")

        (SETUP_DIR / f"{manifest['name']}.setup").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Sail harness
# ---------------------------------------------------------------------------


def _run_sail() -> None:
    shutil.rmtree(SAIL_DUMP_DIR, ignore_errors=True)
    _run(["make", "test"], REPO_ROOT, "Sail `make test`")


def _run_asm_test(test_name: str, manifest: dict) -> None:
    """Compile and run an assembly-only test via the universal_harness."""
    inc_file = INC_DIR / f"{test_name}.inc"
    if not inc_file.exists():
        print(f"[diff] No .inc for {test_name}, skipping HIP run.")
        return

    bin_dir = HIP_OUTPUT_DIR / "binaries"
    bin_dir.mkdir(parents=True, exist_ok=True)
    co_path = bin_dir / f"{test_name}.co"
    include_dir = REPO_ROOT / "bare_metal_test" / "harness" / "include"
    harness_bin = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"

    dump_asm = _generate_dump_logic(manifest)
    dump_inc_path = PYTEST_BUILD_DIR / f"{test_name}_dump.inc"
    PYTEST_BUILD_DIR.mkdir(exist_ok=True)
    dump_inc_path.write_text(dump_asm)

    print(f"[diff] Compiling .co for {test_name} (asm path)...")
    _run([
        "hipcc",
        "--offload-arch=gfx1101",
        "--cuda-device-only",
        f"-I{include_dir.resolve()}",
        f'-DTEST_INC="{inc_file.resolve()}"',
        f'-DDUMP_INC="{dump_inc_path.resolve()}"',
        str(REPO_ROOT / "bare_metal_test" / "harness" / "kernel.hip"),
        "-o", str(co_path),
    ], REPO_ROOT, f"Compile {test_name}.co")

    # Point the manifest's binary_path at the freshly-built .co
    manifest_copy = {**manifest, "binary_path": str(co_path)}
    run_manifest = PYTEST_BUILD_DIR / f"{test_name}_run.json"
    run_manifest.write_text(json.dumps(manifest_copy))

    print(f"[diff] Running {test_name} on GPU (asm path)...")
    _run([str(harness_bin), str(run_manifest)], REPO_ROOT, f"Run {test_name}")

    # universal_harness writes to outputs/ — move to HIP_OUTPUT_DIR
    for gen in (REPO_ROOT / "outputs").glob(f"{test_name}_*registers"):
        shutil.move(str(gen), str(HIP_OUTPUT_DIR / gen.name))


def _run_hip_kernel(test_name: str, manifest: dict) -> None:
    """Instrument, compile, and run a standalone C++ kernel."""
    src_path = KERNEL_DIR / f"{test_name}.hip"
    if not src_path.exists():
        return

    PYTEST_BUILD_DIR.mkdir(exist_ok=True)

    kernel_name = manifest.get("kernel_name", test_name)
    capture_prefix = manifest.get("capture_prefix", "v")
    vgpr_indices = manifest["registers"]["vgprs"]["indices"]
    num_vgprs = manifest["registers"]["vgprs"]["count"]
    vgpr_elems = num_vgprs * WAVE_SIZE
    initial_mem = manifest.get("initial_memory_hex", [])

    # Read user's kernel source and inject dump logic at the DUMP_HOOK
    kernel_code = src_path.read_text()
    dump_asm = _generate_dump_logic(manifest)
    kernel_code = kernel_code.replace(
        'asm volatile("// DUMP_HOOK");',
        f"asm volatile(\n{dump_asm}\n);",
    )

    # Build the mem_buf initialiser
    mem_init_lines = "\n".join(
        f"    h_mem[{i}] = 0x{val};"
        for i, val in enumerate(initial_mem)
    )

    # Build the text-format output writer (matches parse.py expectations)
    write_lines: list[str] = []
    for i, reg_idx in enumerate(vgpr_indices):
        write_lines.append(
            f'    out << "{capture_prefix}{reg_idx}:";'
        )
        write_lines.append(
            f"    for (int lane = 0; lane < {WAVE_SIZE}; lane++)"
        )
        write_lines.append(
            f'        out << " " << std::hex << std::setfill(\'0\')'
            f" << std::setw(8)"
            f" << static_cast<unsigned>(h_vgpr[{i} * {WAVE_SIZE} + lane]);"
        )
        write_lines.append('    out << "\\n";')
    write_code = "\n".join(write_lines)

    out_file = HIP_OUTPUT_DIR / f"{test_name}_vector_registers"

    instrumented = f"""\
#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <cstring>
#include <hip/hip_runtime.h>

{kernel_code}

int main() {{
    constexpr int WAVE_SIZE = {WAVE_SIZE};
    constexpr int MEM_BUF_INT = 64;
    int vgpr_elems = {vgpr_elems};

    std::vector<int> h_mem(MEM_BUF_INT, 0);
{mem_init_lines}

    int *d_vgpr, *d_sgpr, *d_mem;
    hipMalloc(&d_vgpr, vgpr_elems * sizeof(int));
    hipMalloc(&d_sgpr, sizeof(int));
    hipMalloc(&d_mem, MEM_BUF_INT * sizeof(int));

    hipMemset(d_vgpr, 0, vgpr_elems * sizeof(int));
    hipMemset(d_sgpr, 0, sizeof(int));
    hipMemcpy(d_mem, h_mem.data(), MEM_BUF_INT * sizeof(int), hipMemcpyHostToDevice);

    {kernel_name}<<<1, WAVE_SIZE>>>(d_vgpr, d_sgpr, d_mem);
    hipDeviceSynchronize();

    std::vector<int> h_vgpr(vgpr_elems);
    hipMemcpy(h_vgpr.data(), d_vgpr, vgpr_elems * sizeof(int), hipMemcpyDeviceToHost);

    std::ofstream out("{out_file}");
{write_code}

    hipFree(d_vgpr);
    hipFree(d_sgpr);
    hipFree(d_mem);
    return 0;
}}
"""

    instrumented_src = PYTEST_BUILD_DIR / f"{test_name}_instrumented.hip"
    instrumented_src.write_text(instrumented)

    executable = PYTEST_BUILD_DIR / f"{test_name}_instrumented.out"

    print(f"[diff] Compiling {test_name} (C++ kernel path)...")
    _run(
        ["hipcc", "--offload-arch=gfx1101", str(instrumented_src), "-o", str(executable)],
        REPO_ROOT, f"Compile {test_name}",
    )

    print(f"[diff] Running {test_name} on GPU (C++ kernel path)...")
    _run([str(executable)], REPO_ROOT, f"Run {test_name}")


def _hip_test_names() -> list[str]:
    """Tests with a manifest JSON in tests/manifests/."""
    if not MANIFEST_DIR.exists():
        return []
    return sorted(p.stem for p in MANIFEST_DIR.glob("*.json"))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--skip-run",
        action="store_true",
        default=False,
        help="Skip running harnesses and compare existing output files.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "test_name" not in metafunc.fixturenames:
        return
    metafunc.parametrize("test_name", _hip_test_names())


@pytest.fixture(scope="session", autouse=True)
def run_harnesses(request: pytest.FixtureRequest) -> None:
    """Run Sail + HIP harnesses once per session before any tests execute."""
    if request.config.getoption("--skip-run", default=False):
        return

    print("\n[diff] Generating Sail setup files from manifests...")
    _generate_setup_files()

    print("[diff] Running Sail harness (make test)...")
    _run_sail()

    # Prepare HIP output directory
    shutil.rmtree(HIP_OUTPUT_DIR, ignore_errors=True)
    HIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[diff] Running HIP harnesses...")
    for test_name in _hip_test_names():
        manifest_path = MANIFEST_DIR / f"{test_name}.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        if (KERNEL_DIR / f"{test_name}.hip").exists():
            _run_hip_kernel(test_name, manifest)
        else:
            _run_asm_test(test_name, manifest)

    print("[diff] Both harnesses complete.")

def _run_hip_brute_force() -> None:
    """Captures v0-v27 for every test to check for unintended side effects."""
    shutil.rmtree(HIP_BF_OUTPUT_DIR, ignore_errors=True)
    HIP_BF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    harness_bin = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"

    for manifest_path in MANIFEST_DIR.glob("*.json"):
        with open(manifest_path) as f:
            manifest = json.load(f)

        test_name = manifest["name"]
        manifest["registers"]["vgprs"] = {
            "count": 28,
            "indices": list(range(28)),
        }

        bf_manifest_path = HIP_BF_OUTPUT_DIR / f"{test_name}_bf.json"
        with open(bf_manifest_path, "w") as f:
            json.dump(manifest, f)

        print(f"[brute-force] Running {test_name}...")
        _run([str(harness_bin), str(bf_manifest_path)], REPO_ROOT, f"BF Run {test_name}")

        for gen in (REPO_ROOT / "outputs").glob(f"{test_name}_*registers"):
            shutil.move(str(gen), str(HIP_BF_OUTPUT_DIR / gen.name))

@pytest.fixture(scope="session")
def sail_results(run_harnesses: None) -> dict[str, RegisterDump]:
    return parse.sail_vector_dumps(SAIL_DUMP_DIR)


@pytest.fixture(scope="session")
def sail_scalar_results(run_harnesses: None) -> dict[str, RegisterDump]:
    return parse.sail_scalar_dumps(SAIL_DUMP_DIR)


@pytest.fixture(scope="session")
def sail_all_results(
    sail_results: dict[str, RegisterDump],
    sail_scalar_results: dict[str, RegisterDump],
) -> dict[str, RegisterDump]:
    all_names = set(sail_results) | set(sail_scalar_results)
    return {
        name: {**sail_results.get(name, {}), **sail_scalar_results.get(name, {})}
        for name in all_names
    }


@pytest.fixture(scope="session")
def hip_results(run_harnesses: None) -> dict[str, RegisterDump]:
    return parse.hip_vector_dumps(HIP_OUTPUT_DIR)


@pytest.fixture(scope="session")
def run_brute_force(request: pytest.FixtureRequest) -> None:
    if not request.config.getoption("--brute-force", default=False):
        return
    if request.config.getoption("--skip-run", default=False):
        return
    print("\n[brute-force] Building and running HIP brute-force harness...")
    _run_hip_brute_force()
    print("[brute-force] Done.")


@pytest.fixture(scope="session")
def brute_force_hip_results(run_brute_force: None) -> dict[str, RegisterDump]:
    if not HIP_BF_OUTPUT_DIR.exists():
        return {}
    return parse.hip_vector_dumps(HIP_BF_OUTPUT_DIR)


@pytest.fixture(scope="session")
def sail_allowed_nonzero() -> dict[str, frozenset[str]]:
    return _SAIL_ALLOWED_NONZERO

from __future__ import annotations

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
HIP_DIR = REPO_ROOT / "bare_metal_test"
HIP_OUTPUT_DIR = HIP_DIR / "outputs"
HIP_BF_OUTPUT_DIR = HIP_DIR / "outputs_brute_force"
MANIFEST_DIR = REPO_ROOT / "tests" / "manifests"

# ---------------------------------------------------------------------------
# Sentinel register allow-lists
#
# Maps test name -> set of register names that are permitted to be non-zero
# in the Sail full dump after the test runs.  Every other register must be
# zero; if it isn't, the Sail spec is accidentally clobbering it.
#
# Include both the "result" registers AND any scratch registers the test .asm
# uses internally (e.g. address setup registers).  Update this dict whenever
# you add a new test.
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
}

# ---------------------------------------------------------------------------
# Harness runners
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path, label: str) -> None:
    """Run a shell command, streaming its output live.  Raises on failure."""
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")


def _run_sail() -> None:
    shutil.rmtree(SAIL_DUMP_DIR, ignore_errors=True)
    _run(["make", "test"], REPO_ROOT, "Sail `make test`")


def _run_hip() -> None:
    """Dynamically compile and run all hardware tests using the Universal Harness."""
    import json
    
    shutil.rmtree(HIP_OUTPUT_DIR, ignore_errors=True)
    HIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    bin_dir = HIP_OUTPUT_DIR / "binaries"
    bin_dir.mkdir(parents=True, exist_ok=True)

    harness_bin = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"
    kernel_src = REPO_ROOT / "bare_metal_test" / "harness" / "kernel.hip"
    include_dir = REPO_ROOT / "bare_metal_test" / "harness" / "include"

    for manifest_path in MANIFEST_DIR.glob("*.json"):
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        test_name = manifest["name"]
        co_path = bin_dir / f"{test_name}.co"
        inc_file = REPO_ROOT / "bare_metal_test" / "asm" / f"{test_name}.inc"
        dump_file = REPO_ROOT / "bare_metal_test" / "asm" / f"{test_name}_dump.inc"
        hip_file = REPO_ROOT / "bare_metal_test" / "kernels" / f"{test_name}.hip"
        
        if inc_file.exists():
            print(f"[diff] Compiling .co from Assembly for {test_name}...")
            _run([
                "hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
                f"-I{include_dir}",
                f'-DTEST_INC="{inc_file}"',
                f'-DDUMP_INC="{dump_file}"',
                str(kernel_src), "-o", str(co_path)
            ], REPO_ROOT, f"Compile {test_name}.co")
        elif hip_file.exists():
            print(f"[diff] Compiling .co from C++ for {test_name}...")
            _run([
                "hipcc", "--offload-arch=gfx1101", "--cuda-device-only",
                str(hip_file), "-o", str(co_path)
            ], REPO_ROOT, f"Compile {test_name}.co")
        else:
            print(f"[diff] WARNING: Missing source for {test_name}. Skipping compilation.")

        print(f"[diff] Running {test_name} on RX 7800XT...")
        _run([str(harness_bin), str(manifest_path)], REPO_ROOT, f"Run {test_name}")
        
        for generated_file in (REPO_ROOT / "outputs").glob(f"{test_name}_*registers"):
            shutil.move(str(generated_file), str(HIP_OUTPUT_DIR / generated_file.name))

def _run_hip_brute_force() -> None:
    """Captures v0-v27 for every test to check for unintended side effects."""
    import json
    shutil.rmtree(HIP_BF_OUTPUT_DIR, ignore_ok=True)
    HIP_BF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    harness_bin = REPO_ROOT / "bare_metal_test" / "build" / "universal_harness"
    
    for manifest_path in MANIFEST_DIR.glob("*.json"):
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        test_name = manifest["name"]
        manifest["registers"]["vgprs"] = {
            "count": 26,
            "indices": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,16,17,18,19,20,21,22,23,24,25,26,27]
        }
        
        bf_manifest_path = HIP_BF_OUTPUT_DIR / f"{test_name}_bf.json"
        with open(bf_manifest_path, "w") as f:
            json.dump(manifest, f)

        print(f"[brute-force] Running {test_name}...")
        _run([str(harness_bin), str(bf_manifest_path)], REPO_ROOT, f"BF Run {test_name}")
        
        for gen in (REPO_ROOT / "outputs").glob(f"{test_name}_*registers"):
            shutil.move(str(gen), str(HIP_BF_OUTPUT_DIR / gen.name))


# ---------------------------------------------------------------------------
# Test discovery (from source files, so --collect-only works without outputs)
# ---------------------------------------------------------------------------


def _hip_test_names() -> list[str]:
    """Tests with a manifest JSON in tests/manifests/."""
    if not MANIFEST_DIR.exists():
        return []
    return sorted(p.stem for p in MANIFEST_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--skip-run",
        action="store_true",
        default=False,
        help="Skip running harnesses and compare existing output files.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrise test_name over HIP-covered tests. Uses source files so
    --collect-only works without needing outputs to exist first."""
    if "test_name" not in metafunc.fixturenames:
        return
    metafunc.parametrize("test_name", _hip_test_names())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def run_harnesses(request: pytest.FixtureRequest) -> None:
    """Run both test harnesses once per session before any tests execute.
    Skipped when --skip-run is passed or during --collect-only."""
    if request.config.getoption("--skip-run", default=False):
        return
    print("\n[diff] Running Sail harness (make test)...")
    _run_sail()
    print("[diff] Running HIP harness (make run)...")
    _run_hip()
    print("[diff] Both harnesses complete.")


@pytest.fixture(scope="session")
def sail_results(run_harnesses: None) -> dict[str, RegisterDump]:
    """Parsed Sail vector register dumps (vec_*.log), keyed by test name."""
    return parse.sail_vector_dumps(SAIL_DUMP_DIR)


@pytest.fixture(scope="session")
def sail_scalar_results(run_harnesses: None) -> dict[str, RegisterDump]:
    """Parsed Sail scalar register dumps (scal_*.log), keyed by test name."""
    return parse.sail_scalar_dumps(SAIL_DUMP_DIR)


@pytest.fixture(scope="session")
def sail_all_results(
    sail_results: dict[str, RegisterDump],
    sail_scalar_results: dict[str, RegisterDump],
) -> dict[str, RegisterDump]:
    """Merged vector + scalar Sail dumps, keyed by test name."""
    all_names = set(sail_results) | set(sail_scalar_results)
    return {
        name: {**sail_results.get(name, {}), **sail_scalar_results.get(name, {})}
        for name in all_names
    }


@pytest.fixture(scope="session")
def hip_results(run_harnesses: None) -> dict[str, RegisterDump]:
    """Parsed HIP register dumps (*_vector_registers), keyed by test name."""
    return parse.hip_vector_dumps(HIP_OUTPUT_DIR)


@pytest.fixture(scope="session")
def run_brute_force(request: pytest.FixtureRequest) -> None:
    """Build and run the brute-force HIP harness (make brute_force_run).
    Only executes when --brute-force is passed."""
    if not request.config.getoption("--brute-force", default=False):
        return
    if request.config.getoption("--skip-run", default=False):
        return
    print("\n[brute-force] Building and running HIP brute-force harness...")
    _run_hip_brute_force()
    print("[brute-force] Done.")


@pytest.fixture(scope="session")
def brute_force_hip_results(run_brute_force: None) -> dict[str, RegisterDump]:
    """Parsed HIP brute-force dumps (v0-v13, v16-v27), keyed by test name."""
    if not HIP_BF_OUTPUT_DIR.exists():
        return {}
    return parse.hip_vector_dumps(HIP_BF_OUTPUT_DIR)


@pytest.fixture(scope="session")
def sail_allowed_nonzero() -> dict[str, frozenset[str]]:
    """Per-test set of register names permitted to be non-zero in the Sail dump."""
    return _SAIL_ALLOWED_NONZERO

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
    shutil.rmtree(HIP_OUTPUT_DIR, ignore_errors=True)
    _run(["make", "run"], HIP_DIR, "HIP `make run`")


def _run_hip_brute_force() -> None:
    shutil.rmtree(HIP_BF_OUTPUT_DIR, ignore_errors=True)
    _run(["make", "brute_force_run"], HIP_DIR, "HIP `make brute_force_run`")


# ---------------------------------------------------------------------------
# Test discovery (from source files, so --collect-only works without outputs)
# ---------------------------------------------------------------------------


def _hip_test_names() -> list[str]:
    """Tests with a .inc file in bare_metal_test/asm/ (excluding dump files)."""
    asm_dir = HIP_DIR / "asm"
    if not asm_dir.exists():
        return []
    return sorted(p.stem for p in asm_dir.glob("*.inc") if not p.stem.endswith("_dump"))


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

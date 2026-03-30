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

# ---------------------------------------------------------------------------
# Harness runners
# ---------------------------------------------------------------------------


def _run_sail() -> None:
    shutil.rmtree(SAIL_DUMP_DIR, ignore_errors=True)
    result = subprocess.run(["make", "test"], cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Sail `make test` failed:\n{result.stderr}")


def _run_hip() -> None:
    shutil.rmtree(HIP_OUTPUT_DIR, ignore_errors=True)
    result = subprocess.run(["make", "run"], cwd=HIP_DIR, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"HIP `make run` failed:\n{result.stderr}")


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

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
    result = subprocess.run(
        ["make", "test"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Sail `make test` failed:\n{result.stderr}")


def _run_hip() -> None:
    shutil.rmtree(HIP_OUTPUT_DIR, ignore_errors=True)
    result = subprocess.run(
        ["make", "run"],
        cwd=HIP_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HIP `make run` failed:\n{result.stderr}")


# ---------------------------------------------------------------------------
# Test discovery
# ---------------------------------------------------------------------------


def _hip_test_names() -> list[str]:
    """Discover HIP test names from bare_metal_test/asm/*.inc (excluding dump files)."""
    asm_dir = HIP_DIR / "asm"
    if not asm_dir.exists():
        return []
    return sorted(
        p.stem
        for p in asm_dir.glob("*.inc")
        if not p.stem.endswith("_dump")
    )


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


def pytest_configure(config: pytest.Config) -> None:
    if getattr(config.option, "collectonly", False):
        return
    if getattr(config.option, "skip_run", False):
        return
    _run_sail()
    _run_hip()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrise test_name over the intersection of Sail and HIP test coverage."""
    if "test_name" not in metafunc.fixturenames:
        return

    sail_names: set[str] = (
        {p.stem.removeprefix("vec_") for p in SAIL_DUMP_DIR.glob("vec_*.log")}
        if SAIL_DUMP_DIR.exists()
        else set()
    )
    hip_names = set(_hip_test_names())
    common = sorted(sail_names & hip_names)
    metafunc.parametrize("test_name", common)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sail_results() -> dict[str, RegisterDump]:
    return parse.sail_vector_dumps(SAIL_DUMP_DIR)


@pytest.fixture(scope="session")
def hip_results() -> dict[str, RegisterDump]:
    return parse.hip_vector_dumps(HIP_OUTPUT_DIR)

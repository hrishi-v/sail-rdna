"""Pytest configuration for the kernel differential test suite.

Each kernel in kernels/ has a companion fixture in kernels/fixtures/ that
describes its initial register / memory state and how to parse its results.
This suite compiles the kernel, strips its GPU ASM, runs both the Sail
emulator and the real HIP binary, then compares the memory they produce.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
KERNELS_DIR = REPO_ROOT / 'kernels'
FIXTURES_DIR = KERNELS_DIR / 'fixtures'
EMU = REPO_ROOT / 'rdna3_emu'
KERNEL_DUMP_DIR = REPO_ROOT / 'outputs' / 'kernel_dumps'


# ---------------------------------------------------------------------------
# Fixture discovery
# ---------------------------------------------------------------------------

def _kernel_names() -> list[str]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(
        p.stem for p in FIXTURES_DIR.glob('*.py')
        if not p.name.startswith('_')
    )


def _load_fixture(kernel_name: str):
    path = FIXTURES_DIR / f'{kernel_name}.py'
    spec = importlib.util.spec_from_file_location(kernel_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: Path, label: str) -> None:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f'{label} failed (exit {result.returncode})')


def _parse_memory_dump(path: Path) -> list[int]:
    """Parse a ``0xADDRESS: 0xVALUE`` dump file → ordered list of 32-bit values."""
    values = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        _, _, val_str = line.partition(': ')
        values.append(int(val_str.strip(), 16))
    return values


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        '--skip-run',
        action='store_true',
        default=False,
        help='Compare existing output files without re-running any harness.',
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if 'kernel_name' in metafunc.fixturenames:
        metafunc.parametrize('kernel_name', _kernel_names())


# ---------------------------------------------------------------------------
# Session-scoped fixtures  (run once, results cached for all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session', autouse=True)
def run_harnesses(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Build everything and run both harnesses (HIP + Sail) once per session."""
    if request.config.getoption('--skip-run', default=False):
        return

    print('\n[kernels] Building kernels and stripping ASM...')
    _run(
        ['make', 'dump-asm', 'strip-asm', 'assemble-stripped'],
        KERNELS_DIR,
        'make strip-asm / assemble-stripped',
    )

    print('[kernels] Running HIP kernels on hardware...')
    _run(['make', 'run'], KERNELS_DIR, 'make run')

    print('[kernels] Running Sail emulator for each kernel...')
    setup_dir = tmp_path_factory.mktemp('kernel_setups')
    KERNEL_DUMP_DIR.mkdir(parents=True, exist_ok=True)

    for name in _kernel_names():
        fixture = _load_fixture(name)
        setup_file = setup_dir / f'{name}.setup'
        dump_output = KERNEL_DUMP_DIR / f'{name}_memory.log'
        fixture.generate_setup_file(setup_file, dump_output)

        bin_path = KERNELS_DIR / 'stripped' / f'{name}.bin'
        _run(
            [str(EMU), '--kernel-test', str(bin_path), str(setup_file)],
            REPO_ROOT,
            f'rdna3_emu --kernel-test {name}',
        )

    print('[kernels] Both harnesses complete.')


@pytest.fixture(scope='session')
def sail_results(run_harnesses: None) -> dict[str, list[int]]:
    """Parsed Sail memory dumps, keyed by kernel name."""
    results: dict[str, list[int]] = {}
    for name in _kernel_names():
        path = KERNEL_DUMP_DIR / f'{name}_memory.log'
        if path.exists():
            results[name] = _parse_memory_dump(path)
    return results


@pytest.fixture(scope='session')
def hip_results(run_harnesses: None) -> dict[str, list[int]]:
    """Parsed HIP result files, keyed by kernel name."""
    results: dict[str, list[int]] = {}
    for name in _kernel_names():
        fixture = _load_fixture(name)
        path = KERNELS_DIR / 'outputs' / f'{name}_results.log'
        if path.exists():
            results[name] = fixture.parse_hip_output(path)
    return results

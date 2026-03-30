from __future__ import annotations

import random
from pathlib import Path

import pytest

import parse
from generate_program import Program, generate_program, asm_text, hip_dump_inc_text, hip_inc_text
from parse import RegisterDump
from runner import assemble, compile_and_run_hip, run_sail

_FUZZER_DIR = Path(__file__).resolve().parent
_FUZZ_TESTS_DIR = _FUZZER_DIR / "fuzz_tests"
_BUILD_DIR = _FUZZER_DIR.parent / "bare_metal_test" / "build"

# ---------------------------------------------------------------------------
# Seed management
# ---------------------------------------------------------------------------

_SEED_KEY = pytest.StashKey[int]()

def pytest_configure(config: pytest.Config) -> None:
    """Pin the fuzz seed once per session so all hooks see the same value."""
    try:
        if not config.getoption("--fuzz", default=False):
            return
        provided: int | None = config.getoption("--fuzz-seed", default=None)
        seed = provided if provided is not None else random.randrange(2**32)
        config.stash[_SEED_KEY] = seed
        print(f"\n[fuzz] seed={seed}  (re-run with --fuzz-seed={seed} to reproduce)")
    except ValueError:
        pass

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "fuzz_name" not in metafunc.fixturenames:
        return
    if not metafunc.config.getoption("--fuzz", default=False):
        # Zero items → no fuzz tests collected; diff tests unaffected.
        metafunc.parametrize("fuzz_name", [])
        return
    count: int = metafunc.config.getoption("--fuzz-count", default=10)
    metafunc.parametrize("fuzz_name", [f"fuzz_{i:04d}" for i in range(count)])


@pytest.fixture(scope="session")
def _seed(request: pytest.FixtureRequest) -> int:
    return request.config.stash.get(_SEED_KEY, 0)


@pytest.fixture(scope="session")
def fuzz_programs(
    request: pytest.FixtureRequest,
    _seed: int,
) -> dict[str, Program]:
    """Generate all programs for this session and write source files."""
    count: int = request.config.getoption("--fuzz-count", default=10)
    rng = random.Random(_seed)
    _FUZZ_TESTS_DIR.mkdir(parents=True, exist_ok=True)
    programs: dict[str, Program] = {}
    for i in range(count):
        name = f"fuzz_{i:04d}"
        prog = generate_program(rng, name)
        (_FUZZ_TESTS_DIR / f"{name}.asm").write_text(asm_text(prog))
        (_FUZZ_TESTS_DIR / f"{name}.inc").write_text(hip_inc_text(prog))
        (_FUZZ_TESTS_DIR / f"{name}_dump.inc").write_text(hip_dump_inc_text())
        programs[name] = prog
    return programs


@pytest.fixture(scope="session")
def fuzz_sail_results(fuzz_programs: dict[str, Program]) -> dict[str, RegisterDump]:
    """Assemble every fuzz program and run it through the Sail emulator."""
    results: dict[str, RegisterDump] = {}
    for name in fuzz_programs:
        asm = _FUZZ_TESTS_DIR / f"{name}.asm"
        elf = _FUZZ_TESTS_DIR / f"{name}.elf"
        raw = _FUZZ_TESTS_DIR / f"{name}.bin"
        assemble(asm, elf, raw)
        vec, scal = run_sail(raw)
        results[name] = {
            **parse.parse_register_file(vec),
            **parse.parse_register_file(scal),
        }
    return results


@pytest.fixture(scope="session")
def fuzz_hip_results(fuzz_programs: dict[str, Program]) -> dict[str, RegisterDump]:
    """Compile and run every fuzz program on the real GPU via HIP."""
    _BUILD_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, RegisterDump] = {}
    for name in fuzz_programs:
        inc = _FUZZ_TESTS_DIR / f"{name}.inc"
        dump = _FUZZ_TESTS_DIR / f"{name}_dump.inc"
        out = compile_and_run_hip(name, inc, dump, _BUILD_DIR)
        results[name] = parse.parse_register_file(out)
    return results

@pytest.fixture
def fuzz_results(
    fuzz_name: str,
    fuzz_sail_results: dict[str, RegisterDump],
    fuzz_hip_results: dict[str, RegisterDump],
) -> tuple[RegisterDump, RegisterDump]:
    return fuzz_sail_results[fuzz_name], fuzz_hip_results[fuzz_name]

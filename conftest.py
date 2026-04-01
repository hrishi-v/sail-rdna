from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Fuzz CLI options (defined here so they are available to both tests/diff/ and
# fuzzer/ conftest files regardless of which testpath is active).
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--fuzz",
        action="store_true",
        default=False,
        help="Run fuzzer tests instead of the hardcoded differential tests.",
    )
    parser.addoption(
        "--fuzz-count",
        type=int,
        default=10,
        metavar="N",
        help="Number of random programs to generate per fuzz session (default: 10).",
    )
    parser.addoption(
        "--fuzz-seed",
        type=int,
        default=None,
        metavar="SEED",
        help="Random seed for reproducible fuzz runs.  Printed at session start.",
    )
    parser.addoption(
        "--keep-fuzz",
        action="store_true",
        default=False,
        help="Keep generated fuzz files in fuzzer/fuzz_tests/ after the run.",
    )
    parser.addoption(
        "--brute-force",
        action="store_true",
        default=False,
        help="Also run brute-force register comparison (v0-v27 except v14:v15).",
    )


# ---------------------------------------------------------------------------
# When --fuzz is active, skip all tests from tests/diff/ so only the fuzzer
# runs.  Without --fuzz the fuzzer parametrises to zero items (no-op).
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "fuzz: marks tests as part of the fuzz suite")
    config.addinivalue_line(
        "markers",
        "brute_force: marks tests that require --brute-force to run",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    fuzz_active = config.getoption("--fuzz", default=False)
    bf_active = config.getoption("--brute-force", default=False)
    skip_diff = pytest.mark.skip(reason="skipped in --fuzz mode (run without --fuzz to enable)")
    skip_fuzz = pytest.mark.skip(reason="fuzz tests require --fuzz flag")
    skip_bf = pytest.mark.skip(reason="brute-force tests require --brute-force flag")
    for item in items:
        if "tests/diff" in str(item.fspath) and fuzz_active:
            item.add_marker(skip_diff)
        elif item.get_closest_marker("fuzz") and not fuzz_active:
            item.add_marker(skip_fuzz)
        elif item.get_closest_marker("brute_force") and not bf_active:
            item.add_marker(skip_bf)

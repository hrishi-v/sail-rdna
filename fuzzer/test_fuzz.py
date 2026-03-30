from __future__ import annotations

import pytest

from parse import RegisterDump


@pytest.mark.fuzz
def test_fuzz_v0_matches(
    fuzz_name: str,
    fuzz_results: tuple[RegisterDump, RegisterDump],
) -> None:
    """Check v0 agrees across all 32 lanes for the Sail specification and the real GPU."""
    sail, hip = fuzz_results

    assert "v0" in sail, f"[{fuzz_name}] v0 missing from Sail dump"
    assert "v0" in hip, f"[{fuzz_name}] v0 missing from HIP dump"

    assert sail["v0"] == hip["v0"], (
        f"[{fuzz_name}] v0 divergence\n"
        f"  sail: {[hex(v) for v in sail['v0']]}\n"
        f"  hip:  {[hex(v) for v in hip['v0']]}\n"
        f"  asm:  fuzzer/fuzz_tests/{fuzz_name}.asm"
    )

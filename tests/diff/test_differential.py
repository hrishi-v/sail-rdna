from __future__ import annotations

from parse import RegisterDump


def test_vgpr_values_match(
    test_name: str,
    sail_results: dict[str, RegisterDump],
    hip_results: dict[str, RegisterDump],
) -> None:
    """For each register captured by the HIP harness, assert all 32 lanes match Sail.

    HIP only dumps the registers declared in VGPR_INDICES, so we compare only those —
    Sail dumps everything but we don't assert on registers the HIP side didn't capture.
    """
    assert test_name in sail_results, f"No Sail output found for '{test_name}'"
    assert test_name in hip_results, f"No HIP output found for '{test_name}'"

    sail = sail_results[test_name]
    hip = hip_results[test_name]

    for reg, hip_lanes in hip.items():
        assert reg in sail, (
            f"[{test_name}] {reg} present in HIP output but missing from Sail dump"
        )
        sail_lanes = sail[reg]
        assert sail_lanes == hip_lanes, (
            f"[{test_name}] {reg} mismatch\n"
            f"  sail: {[hex(v) for v in sail_lanes]}\n"
            f"  hip:  {[hex(v) for v in hip_lanes]}"
        )

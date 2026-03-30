from __future__ import annotations

from parse import RegisterDump


def test_vgpr_values_match(
    test_name: str,
    sail_all_results: dict[str, RegisterDump],
    hip_results: dict[str, RegisterDump],
) -> None:
    """For each register captured by HIP, assert all lanes match Sail.

    Sail vector dumps have 32 lane values; scalar dumps have 1 value (broadcast
    across all lanes). HIP always produces 32 values via flat_store_b32.
    Both cases are handled below.
    """
    assert test_name in sail_all_results, f"No Sail output found for '{test_name}'"
    assert test_name in hip_results, f"No HIP output found for '{test_name}'"

    sail = sail_all_results[test_name]
    hip = hip_results[test_name]

    for reg, hip_lanes in hip.items():
        assert reg in sail, (
            f"[{test_name}] {reg} in HIP output but missing from Sail dump"
        )
        sail_val = sail[reg]

        if len(sail_val) == 1:
            # Scalar: Sail has one value, HIP broadcast it to all 32 lanes.
            expected = sail_val[0]
            mismatches = [
                (lane, v) for lane, v in enumerate(hip_lanes) if v != expected
            ]
            assert not mismatches, (
                f"[{test_name}] {reg} (scalar) mismatch — sail: {hex(expected)}, "
                f"hip lanes differ: {[(l, hex(v)) for l, v in mismatches]}"
            )
        else:
            assert sail_val == hip_lanes, (
                f"[{test_name}] {reg} mismatch\n"
                f"  sail: {[hex(v) for v in sail_val]}\n"
                f"  hip:  {[hex(v) for v in hip_lanes]}"
            )

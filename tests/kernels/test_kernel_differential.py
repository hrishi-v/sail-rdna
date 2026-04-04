from __future__ import annotations


def test_memory_matches(
    kernel_name: str,
    sail_results: dict[str, list[int]],
    hip_results: dict[str, list[int]],
) -> None:
    """Assert Sail and hardware write identical values to output memory.

    Both sides are given the same initial memory state (defined in the kernel's
    fixture).  After execution, the output array must be bit-for-bit identical.
    Any divergence means either the Sail spec computes a wrong value or
    writes to the wrong address.
    """
    assert kernel_name in sail_results, f'No Sail output found for {kernel_name!r}'
    assert kernel_name in hip_results, f'No HIP output found for {kernel_name!r}'

    sail = sail_results[kernel_name]
    hip = hip_results[kernel_name]

    assert len(sail) == len(hip), (
        f'[{kernel_name}] Output length mismatch: sail={len(sail)}, hip={len(hip)}'
    )

    mismatches = [
        (i, sail[i], hip[i]) for i in range(len(sail)) if sail[i] != hip[i]
    ]
    assert not mismatches, (
        f'[{kernel_name}] Memory mismatch at {len(mismatches)} of {len(sail)} positions:\n'
        + '\n'.join(
            f'  [{i:2d}]  sail={hex(s)}  hip={hex(h)}' for i, s, h in mismatches
        )
    )

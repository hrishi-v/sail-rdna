from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import (
    EXP_BUILD_DIR, REPO_ROOT,
    _DUMP_HOOK_PLACEHOLDER, _build_manifest, _compare_dumps,
    _compile_for_sail, _diff, _format_manifest_summary,
    _format_register_dump, _inject_dump_hook, _parse_kernel_name,
    _run_sail_single, _write_setup_file, parse,
)


def test_experimental_pipeline(
    hip_kernel_path: Path,
    experimental_env: None,
    request: pytest.FixtureRequest,
    capsys: pytest.CaptureFixture,
) -> None:
    src = hip_kernel_path.read_text()
    kernel_name = _parse_kernel_name(src)
    assert kernel_name, f"No __global__ kernel function found in {hip_kernel_path}"

    exp_name = f"_exp_{hip_kernel_path.stem}"
    manifest = _build_manifest(exp_name, kernel_name, src)

    instrumented_src = _inject_dump_hook(src)

    # --- Setup file (consumed by Sail's run_test) ---
    setup_path = _diff.SETUP_DIR / f"{exp_name}.setup"
    _write_setup_file(manifest, setup_path)

    # --- Sail side: compile kernel-only .hip to .co, strip to .bin, run ---
    bin_src = _compile_for_sail(instrumented_src, manifest, exp_name)
    sail_bin = REPO_ROOT / "tests" / "bin" / f"{exp_name}.bin"
    shutil.copy(bin_src, sail_bin)

    # --- HIP side: drop instrumented source into tests/kernels/ so that
    #     _run_hip_kernel (which expects src_path = tests/kernels/<name>.hip)
    #     can pick it up. The file still uses the DUMP_HOOK placeholder; the
    #     diff/conftest helper substitutes in the same dump asm for consistency.
    hip_kernel_dst = _diff.KERNEL_DIR / f"{exp_name}.hip"
    hip_kernel_dst.write_text(instrumented_src)

    try:
        _run_sail_single(sail_bin)
        _diff._run_hip_kernel(exp_name, manifest)

        sail_vec = REPO_ROOT / "outputs" / "register_dumps" / f"vec_{exp_name}.log"
        hip_vec = _diff.HIP_OUTPUT_DIR / f"{exp_name}_vector_registers"

        details, status, all_ok = _compare_dumps(manifest, sail_vec, hip_vec)

        sail_reg_lines = (
            _format_register_dump("v", parse.parse_register_file(sail_vec),
                                  manifest["registers"]["vgprs"]["indices"])
            if sail_vec.exists() else ["  <sail dump missing>"]
        )
        hip_reg_lines = (
            _format_register_dump(manifest["capture_prefix"],
                                  parse.parse_register_file(hip_vec),
                                  manifest["registers"]["vgprs"]["indices"])
            if hip_vec.exists() else ["  <hip dump missing>"]
        )

        report = [
            "",
            "=" * 72,
            f"Experimental kernel: {hip_kernel_path}",
            "=" * 72,
            "Auto-generated manifest:",
            *_format_manifest_summary(manifest),
            "",
            "Sail VGPR dump (first 8 lanes):",
            *sail_reg_lines,
            "",
            "HIP VGPR dump (first 8 lanes):",
            *hip_reg_lines,
            "",
            "Per-register comparison:",
            *[f"  {s}" for s in status],
        ]
        if details:
            report.append("")
            report.append("Mismatch details:")
            report.extend(details)
        report.append("=" * 72)

        # Emit report directly so pytest -s prints it, and keep it on the
        # terminal even when the test passes.
        print("\n".join(report))

        assert all_ok, (
            f"Experimental pipeline: {sum('MISMATCH' in s or 'MISSING' in s for s in status)} "
            "register(s) failed -- see report above"
        )
    finally:
        for p in (sail_bin, setup_path, hip_kernel_dst):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

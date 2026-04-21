from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import (
    EXP_BUILD_DIR, REPO_ROOT,
    _build_manifest, _compare_dumps, _compile_for_sail, _diff,
    _format_manifest_summary, _format_register_dump,
    _inject_dump_hook, _parse_kernel_name,
    _run_hip_experimental, _run_sail_single, _write_setup_file, parse,
)
from conftest import _detect_capture_prefix, _detect_vgprs


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
    instrumented_src = _inject_dump_hook(src)

    vgprs = _detect_vgprs(src)
    capture_prefix = _detect_capture_prefix(src)

    # Compile first so we can read the emitted AMDGPU metadata note.
    bin_src, elf_path = _compile_for_sail(
        instrumented_src, exp_name, kernel_name,
        vgpr_indices=vgprs, capture_prefix=capture_prefix,
    )

    manifest = _build_manifest(exp_name, kernel_name, src, elf_path)

    setup_path = _diff.SETUP_DIR / f"{exp_name}.setup"
    _write_setup_file(manifest, setup_path)

    sail_bin = REPO_ROOT / "tests" / "bin" / f"{exp_name}.bin"
    shutil.copy(bin_src, sail_bin)

    try:
        _run_sail_single(sail_bin)
        _run_hip_experimental(manifest, instrumented_src)

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

        print("\n".join(report))

        assert all_ok, (
            f"Experimental pipeline: {sum('MISMATCH' in s or 'MISSING' in s for s in status)} "
            "register(s) failed -- see report above"
        )
    finally:
        for p in (sail_bin, setup_path):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

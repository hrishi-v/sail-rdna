"""Score the negative class: run unmodified (compiler-output) kernels through
the Sail oracle and record any [HAZARD] diagnostics.

Reuses infrastructure from tests/mutation/run_mutation.py.

Output: results/negative_class.csv
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ASM_DIR = REPO / "tests" / "generated" / "asm"
HIP_DIR = REPO / "tests" / "fuzzer" / "generated"
MANIFEST = HIP_DIR / "manifest.json"
RESULTS_CSV = REPO / "tests" / "fuzzer" / "results.csv"
BIN_DIR = REPO / "tests" / "bin"
SETUP_DIR = REPO / "tests" / "setups"
EMU = REPO / "rdna3_emu"
OUT_CSV = REPO / "results" / "negative_class.csv"

sys.path.insert(0, str(REPO / "tests" / "experimental"))
import conftest as exp  # noqa: E402

HAZARD_RE = re.compile(r"\[(?:HAZARD|DIAG)\][^\n]*")


def _silent_run(cmd, cwd, label, timeout=60):
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout,
                       capture_output=True, text=True)
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-400:]
        raise RuntimeError(f"{label} failed (exit {p.returncode}): {tail}")


exp._diff._run = _silent_run


def _load_sail_ok() -> list[str]:
    with RESULTS_CSV.open() as f:
        return [r["kernel"] for r in csv.DictReader(f)
                if r["compile"] == "ok" and r["sail"] == "ok"]


def _load_family_map() -> dict[str, str]:
    with MANIFEST.open() as f:
        return {e["name"]: e["template"] for e in json.load(f)}


def _assemble(asm_path: Path, stem: str) -> Path:
    elf_path = REPO / "tests" / "mutation" / "build" / f"{stem}.elf"
    bin_path = BIN_DIR / f"{stem}.bin"
    elf_path.parent.mkdir(parents=True, exist_ok=True)
    _silent_run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         "-c", str(asm_path), "-o", str(elf_path)],
        REPO, f"clang {stem}",
    )
    _silent_run(
        ["llvm-objcopy", "-O", "binary", "-j", ".text",
         str(elf_path), str(bin_path)],
        REPO, f"objcopy {stem}",
    )
    return bin_path


def _build_setup(kernel: str) -> Path | None:
    hip_path = HIP_DIR / f"{kernel}.hip"
    if not hip_path.exists():
        return None
    src = hip_path.read_text()
    kernel_name = exp._parse_kernel_name(src)
    if not kernel_name:
        return None
    asm_path = ASM_DIR / f"{kernel}.s"
    stem = f"_neg_{kernel}"
    elf_path = REPO / "tests" / "mutation" / "build" / f"{stem}.elf"
    elf_path.parent.mkdir(parents=True, exist_ok=True)
    _silent_run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         "-c", str(asm_path), "-o", str(elf_path)],
        REPO, f"clang {stem}",
    )
    manifest = exp._build_manifest(stem, kernel_name, src, elf_path)
    setup_path = SETUP_DIR / f"{stem}.setup"
    exp._write_setup_file(manifest, setup_path)
    return setup_path


def _run_emu(bin_path: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run([str(EMU), str(bin_path)], cwd=REPO,
                           capture_output=True, text=True, errors="replace",
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return (-1, f"timeout after {timeout}s")
    return (p.returncode, (p.stdout or "") + (p.stderr or ""))


def main():
    if not EMU.exists():
        subprocess.run(["make", "emu"], cwd=REPO, check=True)

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    SETUP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    kernels = _load_sail_ok()
    families = _load_family_map()
    print(f"Scoring {len(kernels)} unmodified kernels", flush=True)

    fields = ["kernel", "family", "num_hazards", "hazard_messages"]
    rows: list[dict] = []
    skipped: list[tuple[str, str]] = []
    cleanup_stems: list[str] = []

    for i, kernel in enumerate(kernels, 1):
        asm_path = ASM_DIR / f"{kernel}.s"
        if not asm_path.exists():
            skipped.append((kernel, "no .s"))
            continue

        try:
            setup = _build_setup(kernel)
        except Exception as e:
            skipped.append((kernel, str(e)[:200]))
            continue
        if setup is None:
            skipped.append((kernel, "setup failed"))
            continue

        stem = f"_neg_{kernel}"
        try:
            bin_path = _assemble(asm_path, stem)
        except Exception as e:
            skipped.append((kernel, str(e)[:200]))
            continue
        cleanup_stems.append(stem)

        rc, blob = _run_emu(bin_path)
        hazards = [h.strip() for h in HAZARD_RE.findall(blob)]

        family = families.get(kernel, "unknown")
        rows.append({
            "kernel": kernel,
            "family": family,
            "num_hazards": len(hazards),
            "hazard_messages": " | ".join(hazards) if hazards else "",
        })
        status = "CLEAN" if not hazards else f"HAZARD({len(hazards)})"
        print(f"[{i}/{len(kernels)}] {kernel} ({family}): {status}", flush=True)

    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Cleanup temp binaries
    for s in cleanup_stems:
        for p in (BIN_DIR / f"{s}.bin", SETUP_DIR / f"{s}.setup"):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    total = len(rows)
    clean = sum(1 for r in rows if r["num_hazards"] == 0)
    flagged = sum(1 for r in rows if r["num_hazards"] > 0)
    print()
    print(f"Total scored : {total}")
    print(f"Clean (0 hazards): {clean}")
    print(f"Flagged (>0 hazards): {flagged}")
    if skipped:
        print(f"Skipped: {len(skipped)}")
        for k, reason in skipped[:10]:
            print(f"  {k}: {reason}")
    print(f"Output: {OUT_CSV}")


if __name__ == "__main__":
    main()

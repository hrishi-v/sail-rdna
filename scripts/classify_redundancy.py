"""Classify BM-tested mutants as load-bearing or redundant.

For each mutant whose s_waitcnt was deleted, runs the *original* (unmutated)
kernel through the Sail emulator with enriched tracing, captures the queue
state at the moment the deleted waitcnt would have executed, and applies a
kind-specific classification rule:

    vmcnt:    load_bearing if vmcnt > 0 OR vlq_count > 0
    lgkmcnt:  load_bearing if plq_count > 0 OR ds_pending > 0
    vscnt:    load_bearing if vscnt > 0
                 else redundant

Operates on two populations:
    - 883 BM-match mutants    (silicon match; redundancy classification target)
    - 276 BM-divergent mutants (silicon diverged; consistency-check validation)
A redundant classification on any BM-divergent mutant indicates a methodology
bug and should halt the analysis.

Methodology precondition: every kernel in the corpus is straight-line
(no s_branch / s_cbranch_*). This guarantees the Nth source-order s_waitcnt
is the Nth executed s_waitcnt, so we can pair source lines with trace events
by sequential index. If branches are added to the corpus, this invariant
fails and the script must fall back to objdump line-to-PC mapping.

Output: results/redundancy_classification.csv
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
MUT_CSV = REPO / "tests" / "mutation" / "mutation_results.csv"
BM_CSV = REPO / "tests" / "mutation" / "bare_metal_diff.csv"
MANIFEST = HIP_DIR / "manifest.json"
BIN_DIR = REPO / "tests" / "bin"
SETUP_DIR = REPO / "tests" / "setups"
EMU = REPO / "rdna3_emu"
OUT_CSV = REPO / "results" / "redundancy_classification.csv"

sys.path.insert(0, str(REPO / "tests" / "experimental"))
import conftest as exp  # noqa: E402

WAITCNT_RE = re.compile(r"^\s*(s_waitcnt_vscnt|s_waitcnt_lgkmcnt|s_waitcnt)\b")
TRACE_WAITCNT_RE = re.compile(r"\| Inst: 0x(BF89|BC7C)")
TRACE_QUEUE_RE = re.compile(
    r"VMCNT:\s*(\d+)\s*\|\s*VLQ:\s*(\d+)\s*\|\s*PLQ:\s*(\d+)"
    r"\s*\|\s*DS_PENDING:\s*(\d+)\s*\|\s*VSCNT:\s*(\d+)"
)


def _silent_run(cmd, cwd, label, timeout=60):
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout,
                       capture_output=True, text=True)
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-400:]
        raise RuntimeError(f"{label} failed (exit {p.returncode}): {tail}")


exp._diff._run = _silent_run


def _load_family_map() -> dict[str, str]:
    with MANIFEST.open() as f:
        return {e["name"]: e["template"] for e in json.load(f)}


def _bm_outcome(mutant_matches_original: str) -> str | None:
    v = mutant_matches_original.strip()
    if v == "yes":
        return "match"
    if v == "no":
        return "divergent"
    return None  # skip / blank


def _load_bm_tested() -> list[dict]:
    bm_idx: dict[tuple[str, int], str] = {}
    with BM_CSV.open() as f:
        for r in csv.DictReader(f):
            outcome = _bm_outcome(r.get("mutant_matches_original", ""))
            if outcome is None:
                continue
            try:
                key = (r["kernel"], int(r["waitcnt_line"]))
            except (KeyError, ValueError):
                continue
            bm_idx[key] = outcome

    rows: list[dict] = []
    with MUT_CSV.open() as f:
        for r in csv.DictReader(f):
            try:
                key = (r["kernel"], int(r["waitcnt_line"]))
            except (KeyError, ValueError):
                continue
            if key not in bm_idx:
                continue
            rows.append({
                "kernel": r["kernel"],
                "waitcnt_line": int(r["waitcnt_line"]),
                "waitcnt_kind": r["waitcnt_kind"],
                "bm_outcome": bm_idx[key],
            })
    return rows


def _source_waitcnt_lines(asm_path: Path) -> list[int]:
    lines = []
    for i, ln in enumerate(asm_path.read_text().splitlines(), 1):
        if WAITCNT_RE.match(ln):
            lines.append(i)
    return lines


def _run_and_extract(kernel: str) -> list[tuple[int, int, int, int, int]]:
    """Run original kernel; return ordered list of
    (vmcnt, vlq, plq, ds_pending, vscnt) at each executed s_waitcnt."""
    asm_path = ASM_DIR / f"{kernel}.s"
    hip_path = HIP_DIR / f"{kernel}.hip"
    src = hip_path.read_text()
    kn = exp._parse_kernel_name(src)

    stem = f"_rc_{kernel}"
    elf_path = REPO / "tests" / "mutation" / "build" / f"{stem}.elf"
    elf_path.parent.mkdir(parents=True, exist_ok=True)
    _silent_run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         "-c", str(asm_path), "-o", str(elf_path)],
        REPO, f"clang {stem}",
    )
    bin_path = BIN_DIR / f"{stem}.bin"
    _silent_run(
        ["llvm-objcopy", "-O", "binary", "-j", ".text",
         str(elf_path), str(bin_path)],
        REPO, f"objcopy {stem}",
    )
    manifest = exp._build_manifest(stem, kn, src, elf_path)
    setup_path = SETUP_DIR / f"{stem}.setup"
    exp._write_setup_file(manifest, setup_path)

    subprocess.run([str(EMU), str(bin_path)], cwd=REPO,
                   capture_output=True, text=True, errors="replace",
                   timeout=120)

    trace_path = REPO / "outputs" / "instruction_trace" / f"{stem}.log"
    trace = trace_path.read_text()

    queues: list[tuple[int, int, int, int, int]] = []
    for line in trace.splitlines():
        if TRACE_WAITCNT_RE.search(line):
            m = TRACE_QUEUE_RE.search(line)
            if not m:
                raise RuntimeError(
                    f"Trace line for {kernel} matches waitcnt opcode but not "
                    f"5-counter format. Line: {line}"
                )
            queues.append((int(m.group(1)), int(m.group(2)),
                           int(m.group(3)), int(m.group(4)),
                           int(m.group(5))))

    for p_clean in (bin_path, setup_path):
        try:
            p_clean.unlink()
        except FileNotFoundError:
            pass

    return queues


def _classify(kind: str, vmcnt: int, vlq: int, plq: int,
              ds_pending: int, vscnt: int) -> str:
    if kind == "vmcnt":
        return "load_bearing" if (vmcnt > 0 or vlq > 0) else "redundant"
    if kind == "lgkmcnt":
        return "load_bearing" if (plq > 0 or ds_pending > 0) else "redundant"
    if kind == "vscnt":
        return "load_bearing" if vscnt > 0 else "redundant"
    raise ValueError(f"unknown waitcnt_kind: {kind}")


def main():
    families = _load_family_map()
    mutants = _load_bm_tested()
    n_match = sum(1 for r in mutants if r["bm_outcome"] == "match")
    n_div = sum(1 for r in mutants if r["bm_outcome"] == "divergent")
    kernels_needed = sorted(set(r["kernel"] for r in mutants))

    print(f"Classifying {len(mutants)} BM-tested mutants "
          f"({n_match} match, {n_div} divergent) "
          f"across {len(kernels_needed)} kernels", flush=True)

    kernel_queue_seq: dict[str, list[tuple[int, int, int, int, int]]] = {}
    kernel_source_lines: dict[str, list[int]] = {}

    for kernel in kernels_needed:
        asm_path = ASM_DIR / f"{kernel}.s"
        kernel_source_lines[kernel] = _source_waitcnt_lines(asm_path)
        kernel_queue_seq[kernel] = _run_and_extract(kernel)
        n_src = len(kernel_source_lines[kernel])
        n_trace = len(kernel_queue_seq[kernel])
        if n_src != n_trace:
            raise RuntimeError(
                f"Alignment failure for {kernel}: "
                f"{n_src} source waitcnts vs {n_trace} trace waitcnts. "
                f"Methodology precondition (straight-line kernel) violated."
            )
        print(f"  {kernel}: {n_src} waitcnts aligned", flush=True)

    fields = [
        "mutant_id", "kernel", "family", "deleted_line", "deleted_inst",
        "waitcnt_kind", "vmcnt", "vlq_count", "plq_count", "ds_pending",
        "vscnt", "classification", "bm_outcome",
    ]
    rows: list[dict] = []

    for r in mutants:
        kernel = r["kernel"]
        line = r["waitcnt_line"]
        kind = r["waitcnt_kind"]
        src_lines = kernel_source_lines[kernel]
        try:
            src_idx = src_lines.index(line)
        except ValueError:
            print(f"  WARN: line {line} not in waitcnt list for {kernel}",
                  file=sys.stderr)
            continue

        vmcnt, vlq, plq, ds_pending, vscnt = kernel_queue_seq[kernel][src_idx]
        deleted_inst = (
            (ASM_DIR / f"{kernel}.s")
            .read_text().splitlines()[line - 1].strip()
        )
        classification = _classify(kind, vmcnt, vlq, plq, ds_pending, vscnt)

        rows.append({
            "mutant_id": f"{kernel}__L{line}",
            "kernel": kernel,
            "family": families.get(kernel, "unknown"),
            "deleted_line": line,
            "deleted_inst": deleted_inst,
            "waitcnt_kind": kind,
            "vmcnt": vmcnt,
            "vlq_count": vlq,
            "plq_count": plq,
            "ds_pending": ds_pending,
            "vscnt": vscnt,
            "classification": classification,
            "bm_outcome": r["bm_outcome"],
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"\nWrote {len(rows)} classifications to {OUT_CSV}")


if __name__ == "__main__":
    main()

"""Join Sail mutation results with bare-metal divergence outcomes.

Inputs:
  tests/mutation/mutation_results.csv   -- per-mutant Sail outcome
  --bm <path>                           -- per-mutant bare-metal diff outcome
  --out-dir <path>                      -- where to write artefacts
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MUT = REPO / "tests" / "mutation" / "mutation_results.csv"


def _hazard_bool(row: dict) -> str:
    return "yes" if row.get("new_hazard_detected", "").strip() == "yes" else "no"


def _bm_status(row: dict) -> str:
    v = row.get("mutant_matches_original", "").strip()
    if v == "yes":
        return "match"
    if v == "no":
        return "diverge"
    return "skip"


def _meaning(hz: str, bm: str) -> str:
    if hz == "yes" and bm == "diverge":
        return "true_positive"
    if hz == "yes" and bm == "match":
        return "compiler_contract_violation_no_observable_corruption"
    if hz == "no" and bm == "diverge":
        return "missed_hazard"
    if hz == "no" and bm == "match":
        return "true_negative"
    return f"undetermined_{bm}"


def _matrix_rows(records: list[dict]) -> tuple[list[dict], dict]:
    counts: Counter = Counter()
    for r in records:
        counts[(r["hazard"], r["bm"])] += 1
    cells = []
    for hz in ("yes", "no"):
        for bm in ("diverge", "match", "skip"):
            cells.append({
                "hazard_fired": hz,
                "bare_metal": bm,
                "count": counts[(hz, bm)],
                "meaning": _meaning(hz, bm),
            })
    tp = counts[("yes", "diverge")]
    fp = counts[("yes", "match")]
    fn = counts[("no", "diverge")]
    tn = counts[("no", "match")]
    sk = counts[("yes", "skip")] + counts[("no", "skip")]
    determined = tp + fp + fn + tn
    metrics = {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "skip": sk, "total": len(records),
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "determined": determined,
    }
    return cells, metrics


def _print_matrix(label: str, cells: list[dict], m: dict) -> None:
    print(f"=== {label} ===")
    print(f"{'':<14} {'diverge':>10} {'match':>10} {'skip':>10}")
    for hz in ("yes", "no"):
        row = {c["bare_metal"]: c["count"] for c in cells if c["hazard_fired"] == hz}
        print(f"hazard={hz:<6} {row['diverge']:>10} {row['match']:>10} {row['skip']:>10}")
    print(f"total mutants    : {m['total']}")
    print(f"determined       : {m['determined']} (skip={m['skip']})")
    p = "n/a" if m["precision"] is None else f"{m['precision']:.4f} ({m['tp']}/{m['tp']+m['fp']})"
    r = "n/a" if m["recall"] is None else f"{m['recall']:.4f} ({m['tp']}/{m['tp']+m['fn']})"
    print(f"precision (TP/(TP+FP)): {p}")
    print(f"recall    (TP/(TP+FN)): {r}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bm", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with MUT.open() as f:
        mut_rows = list(csv.DictReader(f))
    with args.bm.open() as f:
        bm_rows = list(csv.DictReader(f))
    bm_idx = {(r["kernel"], int(r["waitcnt_line"])): r for r in bm_rows}

    records = []
    missing = 0
    for r in mut_rows:
        key = (r["kernel"], int(r["waitcnt_line"]))
        if key not in bm_idx:
            missing += 1
            continue
        records.append({
            "kernel": r["kernel"],
            "waitcnt_line": int(r["waitcnt_line"]),
            "waitcnt_kind": r["waitcnt_kind"],
            "hazard": _hazard_bool(r),
            "bm": _bm_status(bm_idx[key]),
            "bm_notes": bm_idx[key].get("notes", ""),
            "mutant_asm_path": r.get("mutant_asm_path", ""),
        })
    if missing:
        print(f"WARN: {missing} mutants in mutation_results lacked bare-metal data", file=sys.stderr)

    # Overall matrix
    cells, m = _matrix_rows(records)
    out_csv = args.out_dir / "precision_matrix.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["hazard_fired", "bare_metal", "count", "meaning"])
        w.writeheader()
        w.writerows(cells)
    _print_matrix("OVERALL precision matrix", cells, m)

    # Per-kind matrix
    by_kind: dict[str, list[dict]] = {}
    for rec in records:
        by_kind.setdefault(rec["waitcnt_kind"], []).append(rec)
    out_kind = args.out_dir / "precision_matrix_by_kind.csv"
    with out_kind.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["waitcnt_kind", "hazard_fired", "bare_metal", "count", "meaning"])
        w.writeheader()
        for kind in sorted(by_kind.keys()):
            kcells, km = _matrix_rows(by_kind[kind])
            for c in kcells:
                row = {"waitcnt_kind": kind, **c}
                w.writerow(row)
            _print_matrix(f"PER-KIND: {kind}  (n={km['total']})", kcells, km)
    # Note: vscnt cell intentionally absent from data; no mutants of that kind
    # were generated by run_mutation.py because the corpus has no s_waitcnt_vscnt
    # in the original kernels.

    # Sample 5 from compiler_contract_violation cell
    fp_records = [r for r in records if r["hazard"] == "yes" and r["bm"] == "match"]
    samples_fp = fp_records[:5]
    fp_csv = args.out_dir / "samples_fp.csv"
    with fp_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kernel", "waitcnt_line", "waitcnt_kind",
                                           "deleted_waitcnt_line", "mutant_asm_path"])
        w.writeheader()
        for r in samples_fp:
            line_text = ""
            asm_path = REPO / "tests" / "generated" / "asm" / f"{r['kernel']}.s"
            if asm_path.exists():
                lines = asm_path.read_text().splitlines()
                if 0 < r["waitcnt_line"] <= len(lines):
                    line_text = lines[r["waitcnt_line"] - 1].strip()
            w.writerow({
                "kernel": r["kernel"],
                "waitcnt_line": r["waitcnt_line"],
                "waitcnt_kind": r["waitcnt_kind"],
                "deleted_waitcnt_line": line_text,
                "mutant_asm_path": r["mutant_asm_path"],
            })

    print(f"=== compiler_contract_violation cell: {len(fp_records)} entries; sampled 5 ===")
    for r in samples_fp:
        line_text = ""
        asm_path = REPO / "tests" / "generated" / "asm" / f"{r['kernel']}.s"
        if asm_path.exists():
            lines = asm_path.read_text().splitlines()
            if 0 < r["waitcnt_line"] <= len(lines):
                line_text = lines[r["waitcnt_line"] - 1].strip()
        print(f"  {r['kernel']} L{r['waitcnt_line']} ({r['waitcnt_kind']}): {line_text}")
    print()

    # All from missed_hazard cell
    fn_records = [r for r in records if r["hazard"] == "no" and r["bm"] == "diverge"]
    fn_csv = args.out_dir / "samples_missed_hazard.csv"
    with fn_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kernel", "waitcnt_line", "waitcnt_kind",
                                           "deleted_waitcnt_line", "mutant_asm_path",
                                           "bm_notes"])
        w.writeheader()
        for r in fn_records:
            line_text = ""
            asm_path = REPO / "tests" / "generated" / "asm" / f"{r['kernel']}.s"
            if asm_path.exists():
                lines = asm_path.read_text().splitlines()
                if 0 < r["waitcnt_line"] <= len(lines):
                    line_text = lines[r["waitcnt_line"] - 1].strip()
            w.writerow({
                "kernel": r["kernel"],
                "waitcnt_line": r["waitcnt_line"],
                "waitcnt_kind": r["waitcnt_kind"],
                "deleted_waitcnt_line": line_text,
                "mutant_asm_path": r["mutant_asm_path"],
                "bm_notes": r["bm_notes"],
            })
    print(f"=== missed_hazard cell: {len(fn_records)} entries ===")
    for r in fn_records:
        line_text = ""
        asm_path = REPO / "tests" / "generated" / "asm" / f"{r['kernel']}.s"
        if asm_path.exists():
            lines = asm_path.read_text().splitlines()
            if 0 < r["waitcnt_line"] <= len(lines):
                line_text = lines[r["waitcnt_line"] - 1].strip()
        print(f"  {r['kernel']} L{r['waitcnt_line']} ({r['waitcnt_kind']}): {line_text}")
        print(f"    bm: {r['bm_notes']}")
    print()

    print("Files:")
    print(f"  {out_csv}")
    print(f"  {out_kind}")
    print(f"  {fp_csv}")
    print(f"  {fn_csv}")


if __name__ == "__main__":
    main()

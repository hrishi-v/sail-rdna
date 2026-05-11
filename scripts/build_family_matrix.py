"""Per-family confusion matrix joining mutation results, bare-metal outcomes,
and negative-class (unmodified kernel) scores.

Produces:
  results/per_family_matrix.csv
  results/per_family_matrix.tex
  results/overall_matrix.csv          (relabelled)
  results/overall_matrix_by_kind.csv  (relabelled)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MUT_CSV = REPO / "tests" / "mutation" / "mutation_results.csv"
NEG_CSV = REPO / "results" / "negative_class.csv"
MANIFEST = REPO / "tests" / "fuzzer" / "generated" / "manifest.json"
OUT_DIR = REPO / "results"

BM_CSV = REPO / "tests" / "mutation" / "bare_metal_diff.csv"


def _load_family_map() -> dict[str, str]:
    with MANIFEST.open() as f:
        return {e["name"]: e["template"] for e in json.load(f)}


def _meaning(hz: str, bm: str) -> str:
    if hz == "yes" and bm == "diverge":
        return "true_positive"
    if hz == "yes" and bm == "match":
        return "contract_violation_runtime_benign"
    if hz == "no" and bm == "diverge":
        return "missed_hazard"
    if hz == "no" and bm == "match":
        return "true_negative"
    return f"undetermined_{bm}"


def _matrix_cells(records: list[dict]) -> tuple[list[dict], dict]:
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
    return cells, {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "skip": sk,
        "total": len(records),
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "determined": determined,
    }


def _print_matrix(label: str, cells: list[dict], m: dict) -> None:
    print(f"\n=== {label} ===")
    print(f"{'':<14} {'diverge':>10} {'match':>10} {'skip':>10}")
    for hz in ("yes", "no"):
        row = {c["bare_metal"]: c["count"] for c in cells if c["hazard_fired"] == hz}
        print(f"hazard={hz:<6} {row['diverge']:>10} {row['match']:>10} {row['skip']:>10}")
    print(f"total            : {m['total']}")
    print(f"determined       : {m['determined']} (skip={m['skip']})")
    p = "n/a" if m["precision"] is None else f"{m['precision']:.4f} ({m['tp']}/{m['tp']+m['fp']})"
    r = "n/a" if m["recall"] is None else f"{m['recall']:.4f} ({m['tp']}/{m['tp']+m['fn']})"
    print(f"precision (TP/(TP+CV)): {p}")
    print(f"recall    (TP/(TP+FN)): {r}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    families = _load_family_map()

    # --- Load mutation results ---
    with MUT_CSV.open() as f:
        mut_rows = list(csv.DictReader(f))

    # --- Load bare-metal results (optional) ---
    bm_idx: dict[tuple[str, int], dict] = {}
    if BM_CSV.exists():
        with BM_CSV.open() as f:
            for r in csv.DictReader(f):
                bm_idx[(r["kernel"], int(r["waitcnt_line"]))] = r

    # --- Load negative class ---
    neg_rows: list[dict] = []
    if NEG_CSV.exists():
        with NEG_CSV.open() as f:
            neg_rows = list(csv.DictReader(f))

    # --- Build mutation records with BM join ---
    mut_records = []
    for r in mut_rows:
        key = (r["kernel"], int(r["waitcnt_line"]))
        bm_row = bm_idx.get(key)
        if bm_row:
            bm_status = "match" if bm_row.get("mutant_matches_original", "").strip() == "yes" else (
                "diverge" if bm_row.get("mutant_matches_original", "").strip() == "no" else "skip")
        else:
            bm_status = "skip"
        hazard = "yes" if r.get("new_hazard_detected", "").strip() == "yes" else "no"
        mut_records.append({
            "kernel": r["kernel"],
            "waitcnt_line": int(r["waitcnt_line"]),
            "waitcnt_kind": r["waitcnt_kind"],
            "hazard": hazard,
            "bm": bm_status,
            "family": families.get(r["kernel"], "unknown"),
        })

    # ========== Overall matrix (relabelled) ==========
    cells, m = _matrix_cells(mut_records)
    out_overall = OUT_DIR / "overall_matrix.csv"
    with out_overall.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["hazard_fired", "bare_metal", "count", "meaning"])
        w.writeheader()
        w.writerows(cells)
    _print_matrix("OVERALL (relabelled)", cells, m)

    # ========== Per-kind matrix (relabelled) ==========
    by_kind: dict[str, list[dict]] = {}
    for rec in mut_records:
        by_kind.setdefault(rec["waitcnt_kind"], []).append(rec)
    out_kind = OUT_DIR / "overall_matrix_by_kind.csv"
    with out_kind.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["waitcnt_kind", "hazard_fired", "bare_metal", "count", "meaning"])
        w.writeheader()
        for kind in sorted(by_kind):
            kcells, km = _matrix_cells(by_kind[kind])
            for c in kcells:
                w.writerow({"waitcnt_kind": kind, **c})
            _print_matrix(f"PER-KIND: {kind}  (n={km['total']})", kcells, km)

    # ========== Per-family table ==========
    # Group mutation data by family
    fam_mut: dict[str, list[dict]] = {}
    for rec in mut_records:
        fam_mut.setdefault(rec["family"], []).append(rec)

    # Group negative class by family
    fam_neg: dict[str, list[dict]] = {}
    for rec in neg_rows:
        fam_neg.setdefault(rec["family"], []).append(rec)

    all_families = sorted(set(list(fam_mut.keys()) + list(fam_neg.keys())))

    fam_fields = [
        "family", "n_kernels", "n_mutants",
        "mutants_caught", "mutants_caught_pct",
        "bm_tested", "bm_diverged", "bm_benign", "bm_skip",
        "n_unmodified", "unmodified_clean_pct",
    ]
    fam_rows = []

    for fam in all_families:
        muts = fam_mut.get(fam, [])
        negs = fam_neg.get(fam, [])
        kernels_in_fam = set(r["kernel"] for r in muts) | set(r["kernel"] for r in negs)
        n_mutants = len(muts)
        caught = sum(1 for r in muts if r["hazard"] == "yes")
        bm_tested = sum(1 for r in muts if r["bm"] != "skip")
        bm_diverged = sum(1 for r in muts if r["bm"] == "diverge")
        bm_benign = sum(1 for r in muts if r["bm"] == "match")
        bm_skip = sum(1 for r in muts if r["bm"] == "skip")
        n_unmod = len(negs)
        unmod_clean = sum(1 for r in negs if int(r["num_hazards"]) == 0)

        fam_rows.append({
            "family": fam,
            "n_kernels": len(kernels_in_fam),
            "n_mutants": n_mutants,
            "mutants_caught": caught,
            "mutants_caught_pct": f"{caught / n_mutants * 100:.1f}" if n_mutants else "n/a",
            "bm_tested": bm_tested,
            "bm_diverged": bm_diverged,
            "bm_benign": bm_benign,
            "bm_skip": bm_skip,
            "n_unmodified": n_unmod,
            "unmodified_clean_pct": f"{unmod_clean / n_unmod * 100:.1f}" if n_unmod else "n/a",
        })

    # Totals row
    tot_kernels = sum(int(r["n_kernels"]) for r in fam_rows)
    tot_mutants = sum(int(r["n_mutants"]) for r in fam_rows)
    tot_caught = sum(int(r["mutants_caught"]) for r in fam_rows)
    tot_bm_tested = sum(int(r["bm_tested"]) for r in fam_rows)
    tot_bm_div = sum(int(r["bm_diverged"]) for r in fam_rows)
    tot_bm_ben = sum(int(r["bm_benign"]) for r in fam_rows)
    tot_bm_skip = sum(int(r["bm_skip"]) for r in fam_rows)
    tot_unmod = sum(int(r["n_unmodified"]) for r in fam_rows)
    tot_unmod_clean = sum(int(r["n_unmodified"]) for r in fam_rows
                          if r["unmodified_clean_pct"] == "100.0")
    fam_rows.append({
        "family": "TOTAL",
        "n_kernels": tot_kernels,
        "n_mutants": tot_mutants,
        "mutants_caught": tot_caught,
        "mutants_caught_pct": f"{tot_caught / tot_mutants * 100:.1f}" if tot_mutants else "n/a",
        "bm_tested": tot_bm_tested,
        "bm_diverged": tot_bm_div,
        "bm_benign": tot_bm_ben,
        "bm_skip": tot_bm_skip,
        "n_unmodified": tot_unmod,
        "unmodified_clean_pct": f"{tot_unmod / tot_unmod * 100:.1f}" if tot_unmod else "n/a",
    })

    # --- CSV ---
    csv_path = OUT_DIR / "per_family_matrix.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fam_fields)
        w.writeheader()
        w.writerows(fam_rows)

    # --- LaTeX ---
    tex_path = OUT_DIR / "per_family_matrix.tex"
    _write_latex(fam_rows, fam_fields, tex_path)

    # --- Print table ---
    print("\n\n=== PER-FAMILY MATRIX ===")
    hdr = f"{'Family':<22} {'Kern':>4} {'Mut':>5} {'Caught':>6} {'%':>6}  {'BM':>4} {'Div':>4} {'Ben':>4} {'Skip':>4}  {'Unmod':>5} {'Clean%':>6}"
    print(hdr)
    print("-" * len(hdr))
    for r in fam_rows:
        print(
            f"{r['family']:<22} {r['n_kernels']:>4} {r['n_mutants']:>5} "
            f"{r['mutants_caught']:>6} {r['mutants_caught_pct']:>6}  "
            f"{r['bm_tested']:>4} {r['bm_diverged']:>4} {r['bm_benign']:>4} {r['bm_skip']:>4}  "
            f"{r['n_unmodified']:>5} {r['unmodified_clean_pct']:>6}"
        )

    print(f"\nFiles:\n  {csv_path}\n  {tex_path}\n  {out_overall}\n  {out_kind}")


def _write_latex(rows: list[dict], fields: list[str], path: Path) -> None:
    # Compact LaTeX table suitable for \input
    tex_cols = [
        ("Family", "family", "l"),
        ("$N_{\\text{kern}}$", "n_kernels", "r"),
        ("$N_{\\text{mut}}$", "n_mutants", "r"),
        ("Caught", "mutants_caught", "r"),
        ("Kill \\%", "mutants_caught_pct", "r"),
        ("$N_{\\text{BM}}$", "bm_tested", "r"),
        ("Div.", "bm_diverged", "r"),
        ("Benign", "bm_benign", "r"),
        ("$N_{\\text{unmod}}$", "n_unmodified", "r"),
        ("Clean \\%", "unmodified_clean_pct", "r"),
    ]
    col_spec = "".join(c[2] for c in tex_cols)
    header = " & ".join(c[0] for c in tex_cols)

    lines = []
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")
    lines.append(f"{header} \\\\")
    lines.append("\\midrule")
    for r in rows:
        if r["family"] == "TOTAL":
            lines.append("\\midrule")
        vals = []
        for _, key, _ in tex_cols:
            v = str(r[key])
            if key == "family":
                v = v.replace("_", "\\_")
                if v == "TOTAL":
                    v = "\\textbf{Total}"
            elif r["family"] == "TOTAL":
                v = f"\\textbf{{{v}}}"
            vals.append(v)
        lines.append(" & ".join(vals) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

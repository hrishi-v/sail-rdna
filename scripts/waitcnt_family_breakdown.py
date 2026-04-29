#!/usr/bin/env python3
"""Family breakdown + accum_and exclusion sanity check for waitcnt corpus.

Reads tests/experiments/results/waitcnt_corpus_events.csv (per-event rows),
classifies each kernel into a family by filename prefix, and produces:

  - results/waitcnt_distribution_excl_accum_and.{pdf,png}
  - results/waitcnt_by_family.csv

Plus stdout: before/after vmcnt N=0 share, and the per-family table sorted
by vmcnt_partial_pct desc.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENTS_CSV = REPO_ROOT / "tests" / "experiments" / "results" / "waitcnt_corpus_events.csv"
OUT_DIR = REPO_ROOT / "results"
OUT_PDF = OUT_DIR / "waitcnt_distribution_excl_accum_and.pdf"
OUT_PNG = OUT_DIR / "waitcnt_distribution_excl_accum_and.png"
OUT_FAMILY_CSV = OUT_DIR / "waitcnt_by_family.csv"

COUNTERS = ("vmcnt", "lgkmcnt", "vscnt")

# Order matters: first match wins.
FAMILY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("mixed_loads",        re.compile(r"^mixed_loads_")),
    ("loop_accum",         re.compile(r"^loop_accum_")),
    ("accum_and",          re.compile(r"^accum_and_")),
    ("accum_or",           re.compile(r"^accum_or_")),
    ("accum_add",          re.compile(r"^accum_add_")),
    ("accum_sub",          re.compile(r"^accum_sub_")),
    ("accum_xor",          re.compile(r"^accum_xor_")),
    ("accum_plain",        re.compile(r"^accum_(\d+)$")),
    ("store_chain",        re.compile(r"^store_chain_")),
    ("storeload",          re.compile(r"^storeload_")),
    ("regs_pressure",      re.compile(r"^regs_pressure_")),
    ("deep_chain",         re.compile(r"^deep_chain_")),
    ("chain",              re.compile(r"^chain_")),
    ("rmw_idx",            re.compile(r"^(rmw_idx_|rmwidx_)")),
    ("rmw",                re.compile(r"^rmw_")),
    ("mixed_const",        re.compile(r"^mixed_")),
    ("two_buf",            re.compile(r"^(two_buf_|twobuf_)")),
    ("load_compute_store", re.compile(r"^load_compute_store_")),
]


def classify(kernel: str) -> str:
    for name, pat in FAMILY_PATTERNS:
        if pat.search(kernel):
            return name
    return "other"


def load_events() -> list[tuple[str, str, str, int]]:
    rows = []
    with open(EVENTS_CSV) as f:
        for row in csv.DictReader(f):
            rows.append((row["file"], row["kernel"], row["counter"], int(row["value"])))
    return rows


def histogram(events, counter: str) -> dict[int, int]:
    h: dict[int, int] = defaultdict(int)
    for _, _, c, v in events:
        if c == counter:
            h[v] += 1
    return dict(h)


def plot_three(data: dict[str, dict[int, int]], pdf: Path, png: Path, title_suffix: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.5), sharex=False)
    for ax, counter in zip(axes, COUNTERS):
        buckets = data.get(counter, {})
        if not buckets:
            ax.set_title(f"{counter} (no occurrences) {title_suffix}")
            ax.set_xlabel("N"); ax.set_ylabel("count")
            continue
        xs = sorted(buckets); ys = [buckets[n] for n in xs]
        ax.bar(xs, ys, width=0.8, color="0.25", edgecolor="black", linewidth=0.3)
        ax.set_yscale("log")
        ax.set_xlabel(f"s_waitcnt {counter}(N) immediate")
        ax.set_ylabel("count (log)")
        total = sum(ys); full_pct = 100.0 * buckets.get(0, 0) / total
        ax.set_title(f"{counter}  (n={total}, N=0 share {full_pct:.1f}%) {title_suffix}")
        ax.set_xlim(-1, max(xs) + 1)
    fig.tight_layout(); fig.savefig(pdf); fig.savefig(png, dpi=160); plt.close(fig)


def n0_share(h: dict[int, int]) -> float:
    t = sum(h.values())
    return 100.0 * h.get(0, 0) / t if t else 0.0


def family_stats(events) -> dict[str, dict]:
    by_family: dict[str, dict] = defaultdict(lambda: {
        "kernels": set(),
        "vmcnt": defaultdict(int),
        "lgkmcnt": defaultdict(int),
        "vscnt": defaultdict(int),
    })
    for _file, kernel, counter, v in events:
        fam = classify(kernel)
        s = by_family[fam]
        s["kernels"].add(kernel)
        if counter in COUNTERS:
            s[counter][v] += 1
    return by_family


def main() -> None:
    events = load_events()

    # Part 1: full vs excluding accum_and
    full = {c: histogram(events, c) for c in COUNTERS}
    excl_events = [e for e in events if classify(e[1]) != "accum_and"]
    excl = {c: histogram(excl_events, c) for c in COUNTERS}

    plot_three(excl, OUT_PDF, OUT_PNG, title_suffix="(excl. accum_and)")

    before = n0_share(full["vmcnt"])
    after = n0_share(excl["vmcnt"])

    # Tail-shape comparison: ratio of partial-tail mass to N=0 mass, and
    # whether the tail max shifted significantly.
    full_partial = sum(c for n, c in full["vmcnt"].items() if n > 0)
    excl_partial = sum(c for n, c in excl["vmcnt"].items() if n > 0)
    full_max = max(full["vmcnt"]) if full["vmcnt"] else 0
    excl_max = max(excl["vmcnt"]) if excl["vmcnt"] else 0

    # Heuristic shape verdict.
    if full_partial == 0 or excl_partial == 0:
        shape = "collapsed"
    else:
        ratio_change = abs(after - before)
        max_change = abs(full_max - excl_max)
        if ratio_change < 5.0 and max_change <= 2:
            shape = "unchanged"
        elif after - before > 15.0:
            shape = "collapsed"
        else:
            shape = "shifted"

    print(
        f"vmcnt N=0 share before exclusion: {before:.2f}%, "
        f"after exclusion: {after:.2f}%. Tail shape: [{shape}]."
    )
    print(f"  (full: partial={full_partial}, max_N={full_max}; "
          f"excl: partial={excl_partial}, max_N={excl_max})")

    # Part 2: per-family breakdown
    fams = family_stats(events)
    rows = []
    for fam, s in fams.items():
        vm_total = sum(s["vmcnt"].values())
        lg_total = sum(s["lgkmcnt"].values())
        vs_total = sum(s["vscnt"].values())
        rows.append({
            "family": fam,
            "n_kernels": len(s["kernels"]),
            "vmcnt_total": vm_total,
            "vmcnt_N0_pct": (100.0 * s["vmcnt"].get(0, 0) / vm_total) if vm_total else 0.0,
            "vmcnt_partial_pct": (100.0 * (vm_total - s["vmcnt"].get(0, 0)) / vm_total) if vm_total else 0.0,
            "vmcnt_max_N": max(s["vmcnt"]) if s["vmcnt"] else 0,
            "lgkmcnt_total": lg_total,
            "lgkmcnt_N0_pct": (100.0 * s["lgkmcnt"].get(0, 0) / lg_total) if lg_total else 0.0,
            "vscnt_total": vs_total,
            "vscnt_N0_pct": (100.0 * s["vscnt"].get(0, 0) / vs_total) if vs_total else 0.0,
        })

    rows.sort(key=lambda r: r["vmcnt_partial_pct"], reverse=True)

    cols = ["family", "n_kernels", "vmcnt_total", "vmcnt_N0_pct",
            "vmcnt_partial_pct", "vmcnt_max_N", "lgkmcnt_total",
            "lgkmcnt_N0_pct", "vscnt_total", "vscnt_N0_pct"]
    with open(OUT_FAMILY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r2 = dict(r)
            for k in ("vmcnt_N0_pct", "vmcnt_partial_pct", "lgkmcnt_N0_pct", "vscnt_N0_pct"):
                r2[k] = f"{r[k]:.2f}"
            w.writerow(r2)

    # Print table
    fmt = ("{family:<20} {n_kernels:>4} | vmcnt n={vmcnt_total:>5} "
           "N0%={vmcnt_N0_pct:>6.2f} part%={vmcnt_partial_pct:>6.2f} "
           "max={vmcnt_max_N:>3} | lgkm n={lgkmcnt_total:>4} "
           "N0%={lgkmcnt_N0_pct:>6.2f} | vsc n={vscnt_total:>4} "
           "N0%={vscnt_N0_pct:>6.2f}")
    print()
    print(fmt.replace(":>6.2f", "").replace(":>4", "").replace(":>5", "")
          .replace(":>3", "").replace(":<20", "")
          .format(family="family", n_kernels="kn", vmcnt_total="vm",
                  vmcnt_N0_pct="vmN0%", vmcnt_partial_pct="vmpart%",
                  vmcnt_max_N="maxN", lgkmcnt_total="lgkm",
                  lgkmcnt_N0_pct="lgN0%", vscnt_total="vsc",
                  vscnt_N0_pct="vsN0%"))
    for r in rows:
        print(fmt.format(**r))

    print(f"\nWrote: {OUT_PDF}")
    print(f"Wrote: {OUT_PNG}")
    print(f"Wrote: {OUT_FAMILY_CSV}")


if __name__ == "__main__":
    main()

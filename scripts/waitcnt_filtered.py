#!/usr/bin/env python3
"""Filter runtime helpers (kernels matching ^__) from the waitcnt corpus,
then regenerate the per-family table and aggregate histogram.

Outputs:
  - results/waitcnt_by_family_filtered.csv
  - results/waitcnt_distribution_filtered.{pdf,png}
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
OUT_FAMILY_CSV = OUT_DIR / "waitcnt_by_family_filtered.csv"
OUT_PDF = OUT_DIR / "waitcnt_distribution_filtered.pdf"
OUT_PNG = OUT_DIR / "waitcnt_distribution_filtered.png"

COUNTERS = ("vmcnt", "lgkmcnt", "vscnt")
RUNTIME_RE = re.compile(r"^__")

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
    return "misc"


def load_events():
    rows = []
    with open(EVENTS_CSV) as f:
        for row in csv.DictReader(f):
            rows.append((row["kernel"], row["counter"], int(row["value"])))
    return rows


def histogram(events, counter):
    h = defaultdict(int)
    for _, c, v in events:
        if c == counter:
            h[v] += 1
    return dict(h)


def plot_three(data, pdf, png):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.5), sharex=False)
    for ax, counter in zip(axes, COUNTERS):
        buckets = data.get(counter, {})
        if not buckets:
            ax.set_title(f"{counter} (no occurrences)")
            ax.set_xlabel("N"); ax.set_ylabel("count")
            ax.set_xticks([]); ax.set_yticks([])
            continue
        total = sum(buckets.values())
        full_pct = 100.0 * buckets.get(0, 0) / total

        # If only N=0 is present, annotate rather than draw a degenerate bar.
        if set(buckets.keys()) == {0}:
            ax.text(0.5, 0.5,
                    f"{counter}: every site is {counter}(0)\n"
                    f"n = {total}, no partial drains observed",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"{counter}  (n={total}, N=0 share 100.0%)")
            continue

        xs = sorted(buckets); ys = [buckets[n] for n in xs]
        ax.bar(xs, ys, width=0.8, color="0.25", edgecolor="black", linewidth=0.3)
        ax.set_yscale("log")
        ax.set_xlabel(f"s_waitcnt {counter}(N) immediate")
        ax.set_ylabel("count (log)")
        ax.set_title(f"{counter}  (n={total}, N=0 share {full_pct:.1f}%)")
        ax.set_xlim(-1, max(xs) + 1)
    fig.tight_layout(); fig.savefig(pdf); fig.savefig(png, dpi=160); plt.close(fig)


def family_stats(events):
    by_family: dict[str, dict] = defaultdict(lambda: {
        "kernels": set(),
        "vmcnt": defaultdict(int),
        "lgkmcnt": defaultdict(int),
        "vscnt": defaultdict(int),
    })
    for kernel, counter, v in events:
        fam = classify(kernel)
        s = by_family[fam]
        s["kernels"].add(kernel)
        if counter in COUNTERS:
            s[counter][v] += 1
    return by_family


def main():
    all_events = load_events()
    runtime = [e for e in all_events if RUNTIME_RE.search(e[0])]
    filt = [e for e in all_events if not RUNTIME_RE.search(e[0])]

    full_vm = histogram(all_events, "vmcnt")
    filt_vm = histogram(filt, "vmcnt")
    rt_vm = histogram(runtime, "vmcnt")

    before_total = sum(full_vm.values())
    after_total = sum(filt_vm.values())
    removed = sum(rt_vm.values())
    before_n0 = 100.0 * full_vm.get(0, 0) / before_total
    after_n0 = 100.0 * filt_vm.get(0, 0) / after_total

    # Family table on filtered events
    fams = family_stats(filt)
    rows = []
    for fam, s in fams.items():
        vm = sum(s["vmcnt"].values()); lg = sum(s["lgkmcnt"].values()); vs = sum(s["vscnt"].values())
        rows.append({
            "family": fam,
            "n_kernels": len(s["kernels"]),
            "vmcnt_total": vm,
            "vmcnt_N0_pct": (100.0 * s["vmcnt"].get(0, 0) / vm) if vm else 0.0,
            "vmcnt_partial_pct": (100.0 * (vm - s["vmcnt"].get(0, 0)) / vm) if vm else 0.0,
            "vmcnt_max_N": max(s["vmcnt"]) if s["vmcnt"] else 0,
            "lgkmcnt_total": lg,
            "lgkmcnt_N0_pct": (100.0 * s["lgkmcnt"].get(0, 0) / lg) if lg else 0.0,
            "vscnt_total": vs,
            "vscnt_N0_pct": (100.0 * s["vscnt"].get(0, 0) / vs) if vs else 0.0,
        })
    rows.sort(key=lambda r: r["vmcnt_partial_pct"], reverse=True)

    cols = ["family", "n_kernels", "vmcnt_total", "vmcnt_N0_pct",
            "vmcnt_partial_pct", "vmcnt_max_N", "lgkmcnt_total",
            "lgkmcnt_N0_pct", "vscnt_total", "vscnt_N0_pct"]
    with open(OUT_FAMILY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            r2 = dict(r)
            for k in ("vmcnt_N0_pct", "vmcnt_partial_pct", "lgkmcnt_N0_pct", "vscnt_N0_pct"):
                r2[k] = f"{r[k]:.2f}"
            w.writerow(r2)

    # Histogram on filtered events
    filt_data = {c: histogram(filt, c) for c in COUNTERS}
    plot_three(filt_data, OUT_PDF, OUT_PNG)

    fmt = ("{family:<20} {n_kernels:>4} | vmcnt n={vmcnt_total:>5} "
           "N0%={vmcnt_N0_pct:>6.2f} part%={vmcnt_partial_pct:>6.2f} "
           "max={vmcnt_max_N:>3} | lgkm n={lgkmcnt_total:>4} "
           "N0%={lgkmcnt_N0_pct:>6.2f} | vsc n={vscnt_total:>4} "
           "N0%={vscnt_N0_pct:>6.2f}")
    print()
    for r in rows:
        print(fmt.format(**r))

    print(
        f"\nvmcnt sites: before={before_total}, after={after_total} "
        f"(removed {removed} runtime-helper sites). "
        f"N=0 share: before={before_n0:.2f}%, after={after_n0:.2f}%."
    )
    print(f"Wrote: {OUT_FAMILY_CSV}")
    print(f"Wrote: {OUT_PDF}")
    print(f"Wrote: {OUT_PNG}")


if __name__ == "__main__":
    main()

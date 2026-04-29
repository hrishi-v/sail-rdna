#!/usr/bin/env python3
"""Plot s_waitcnt immediate-value distributions from corpus stats.

Reads tests/experiments/results/waitcnt_corpus_summary.csv and produces
results/waitcnt_distribution.{pdf,png} plus results/waitcnt_summary.csv.
Also prints a one-line prose summary per counter to stdout.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_CSV = REPO_ROOT / "tests" / "experiments" / "results" / "waitcnt_corpus_summary.csv"
OUT_DIR = REPO_ROOT / "results"
OUT_PDF = OUT_DIR / "waitcnt_distribution.pdf"
OUT_PNG = OUT_DIR / "waitcnt_distribution.png"
OUT_CSV = OUT_DIR / "waitcnt_summary.csv"

COUNTERS = ("vmcnt", "lgkmcnt", "vscnt")


def load() -> dict[str, dict[int, int]]:
    data: dict[str, dict[int, int]] = defaultdict(dict)
    with open(SRC_CSV) as f:
        for row in csv.DictReader(f):
            data[row["counter"]][int(row["value"])] = int(row["count"])
    return data


def write_summary_csv(data: dict[str, dict[int, int]]) -> None:
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["counter", "N", "count", "percent_of_counter"])
        for counter in COUNTERS:
            buckets = data.get(counter, {})
            total = sum(buckets.values())
            for n in sorted(buckets):
                pct = 100.0 * buckets[n] / total if total else 0.0
                w.writerow([counter, n, buckets[n], f"{pct:.2f}"])


def print_prose(data: dict[str, dict[int, int]]) -> None:
    for counter in COUNTERS:
        buckets = data.get(counter, {})
        total = sum(buckets.values())
        full = buckets.get(0, 0)
        partial = total - full
        max_n = max(buckets) if buckets else 0
        if total == 0:
            print(f"{counter}: total=0 (no occurrences)")
            continue
        print(
            f"{counter}: total={total}, "
            f"{counter}(0)={full} ({100.0*full/total:.2f}%), "
            f"partial={partial} ({100.0*partial/total:.2f}%), "
            f"max_N={max_n}"
        )


def plot(data: dict[str, dict[int, int]]) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.5), sharex=False)

    for ax, counter in zip(axes, COUNTERS):
        buckets = data.get(counter, {})
        if not buckets:
            ax.set_title(f"{counter} (no occurrences)")
            ax.set_xlabel("N")
            ax.set_ylabel("count")
            continue
        xs = sorted(buckets)
        ys = [buckets[n] for n in xs]
        ax.bar(xs, ys, width=0.8, color="0.25", edgecolor="black", linewidth=0.3)
        ax.set_yscale("log")
        ax.set_xlabel(f"s_waitcnt {counter}(N) immediate")
        ax.set_ylabel("count (log)")
        total = sum(ys)
        full_pct = 100.0 * buckets.get(0, 0) / total
        ax.set_title(f"{counter}  (n={total}, N=0 share {full_pct:.1f}%)")
        ax.set_xlim(-1, max(xs) + 1)

    fig.tight_layout()
    fig.savefig(OUT_PDF)
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)


def main() -> None:
    data = load()
    write_summary_csv(data)
    plot(data)
    print_prose(data)
    print(f"\nWrote: {OUT_PDF}")
    print(f"Wrote: {OUT_PNG}")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()

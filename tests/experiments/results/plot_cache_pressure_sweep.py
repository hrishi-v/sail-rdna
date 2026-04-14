#!/usr/bin/env python3
"""Plot Crossover_N vs Thrash_Count for each filler instruction.

Usage:
    python3 plot_cache_pressure_sweep.py [csv_path] [out_path]
"""
import sys
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DEFAULT_CSV = HERE / "cache_pressure_sweep.csv"
DEFAULT_OUT = HERE / "cache_pressure_sweep.png"


def load(csv_path):
    series = defaultdict(list)
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            series[row["Fill_Type"]].append(
                (int(row["Thrash_Count"]), int(row["Crossover_N"]))
            )
    for k in series:
        series[k].sort()
    return series


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT

    series = load(csv_path)

    fig, ax = plt.subplots(figsize=(10, 6))
    markers = ["o", "s", "^", "D", "v", "P", "X", "*", "h"]
    for i, (label, points) in enumerate(sorted(series.items())):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, marker=markers[i % len(markers)], label=label, linewidth=1.5)

    ax.set_xscale("symlog", linthresh=64)
    ax.set_xlabel("Cache thrash count (lines evicted before load)")
    ax.set_ylabel("Crossover N (filler instructions to mask latency)")
    ax.set_title("s_load_b32 latency: filler crossover vs cache pressure")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left", ncol=2)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

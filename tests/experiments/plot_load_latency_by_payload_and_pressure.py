#!/usr/bin/env python3
"""
Single-panel PDF plot: load-latency crossover N vs cache pressure for
s_load_b32. Crossover N is invariant across payload sizes (b32/b64/b128
all gave identical results — the K$-line fetch dominates and one line
covers all three payloads), so a single panel is sufficient.

Reads:  outputs/load_latency_crossover.csv
Writes: results/load_latency_by_payload_and_pressure.pdf

Run from repo root:
    python tests/experiments/plot_load_latency_by_payload_and_pressure.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT     = Path(__file__).resolve().parents[2]
OUTPUTS_DIR   = REPO_ROOT / "outputs"
RESULTS_DIR   = REPO_ROOT / "tests" / "experiments" / "results"
CROSSOVER_CSV = OUTPUTS_DIR / "load_latency_crossover.csv"
PDF_PATH      = RESULTS_DIR / "load_latency_by_payload_and_pressure.pdf"

PAYLOAD_ORDER = ["b32", "b64", "b128"]
FILL_ORDER = [
    "s_nop 0",
    "v_nop",
    "s_add_u32 s4,s4,1",
    "s_and_b32 s4,s4,s4",
    "v_add_f32 v3,v3,v3",
    "v_add_u32 v3,v3,v3",
    "v_mul_f32 v3,v3,v3",
    "v_mov_b32 v3,v3",
    "mixed(s_add+v_add_f32)/iter",
]

MARKERS    = ["o", "s", "^", "D", "v", "P", "X", "*", "h"]
LINESTYLES = ["-", "--", "-.", ":", "-", "--", "-.", ":", "-"]
COLORS     = plt.cm.tab10.colors[:9]


def load_data() -> dict[tuple[str, str], list[tuple[int, int]]]:
    """key = (payload, fill); value = list of (pressure, crossover_n)."""
    data: dict[tuple[str, str], list[tuple[int, int]]] = {}
    with open(CROSSOVER_CSV) as f:
        for row in csv.DictReader(f):
            key = (row["payload_size"], row["fill_type"])
            cx = row["crossover_n"]
            if cx == "":
                continue
            data.setdefault(key, []).append((int(row["cache_pressure"]), int(cx)))
    for v in data.values():
        v.sort()
    return data


def main() -> None:
    if not CROSSOVER_CSV.exists():
        raise SystemExit(f"missing input: {CROSSOVER_CSV}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams["pdf.fonttype"]      = 42
    plt.rcParams["ps.fonttype"]       = 42
    plt.rcParams["font.size"]         = 9
    plt.rcParams["axes.titlesize"]    = 9
    plt.rcParams["axes.labelsize"]    = 9
    plt.rcParams["xtick.labelsize"]   = 8
    plt.rcParams["ytick.labelsize"]   = 8
    plt.rcParams["legend.fontsize"]   = 7
    plt.rcParams["axes.spines.top"]   = False
    plt.rcParams["axes.spines.right"] = False

    data = load_data()

    fig, ax = plt.subplots(figsize=(6.5, 3.6))

    payload = "b32"
    for i, fill in enumerate(FILL_ORDER):
        series = data.get((payload, fill), [])
        if not series:
            continue
        xs = [p for p, _ in series]
        ys = [n for _, n in series]
        ax.plot(
            xs, ys,
            marker=MARKERS[i % len(MARKERS)],
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            color=COLORS[i % len(COLORS)],
            markersize=4,
            linewidth=1.0,
            label=fill,
        )

    ax.set_xscale("symlog", linthresh=64)
    ax.set_xlabel("Cache pressure (s_load_b128 thrash count)")
    ax.set_ylabel("Crossover N (fill instrs to mask load)")
    ax.grid(True, which="major", linewidth=0.4, alpha=0.4)

    ax.legend(loc="upper left", ncol=2, frameon=False)
    fig.tight_layout()

    fig.savefig(PDF_PATH, format="pdf", bbox_inches="tight")
    print(f"wrote {PDF_PATH}")


if __name__ == "__main__":
    main()

"""Aggregate per_mutant.csv into summary statistics + adjusted divergence."""
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

ROOT = Path("/home/hrishi/Documents/sail-rdna")
OUT = ROOT / "results/multi_iteration_ce14e7e"
PER_MUT = OUT / "per_mutant.csv"


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


rows = list(csv.DictReader(PER_MUT.open()))
for r in rows:
    r["flip_rate_f"] = float(r["flip_rate"]) if r["flip_rate"] else 0.0
    r["n_eff"] = int(r["n_matched"]) + int(r["n_diverged"])

boundary = [r for r in rows if r["population"] == "boundary"]
stable = [r for r in rows if r["population"] == "random_stable"]


def population_stats(label, group):
    fr = [r["flip_rate_f"] for r in group]
    n_zero = sum(1 for f in fr if f == 0.0)
    n_pos = sum(1 for f in fr if f > 0.0)
    mean = statistics.mean(fr) if fr else 0.0
    median = statistics.median(fr) if fr else 0.0
    sd = statistics.pstdev(fr) if len(fr) > 1 else 0.0
    return {
        "label": label, "n": len(group),
        "mean_flip": mean, "median_flip": median, "sd_flip": sd,
        "n_flip_zero": n_zero, "n_flip_pos": n_pos,
    }


def population_pooled_rate(group):
    total_div = sum(int(r["n_diverged"]) for r in group)
    total_eff = sum(r["n_eff"] for r in group)
    if total_eff == 0:
        return 0.0, 0, 0, (0.0, 0.0)
    p = total_div / total_eff
    return p, total_div, total_eff, wilson(p, total_eff)


s_boundary = population_stats("boundary (n=11)", boundary)
s_stable = population_stats("random_stable (n=40)", stable)

print("=" * 72)
print("MULTI-ITERATION BARE METAL RUN-TO-RUN VARIABILITY")
print("=" * 72)
print()
print("Per-population mean flip rate:")
for s in (s_boundary, s_stable):
    print(f"  {s['label']:30s}  mean={s['mean_flip']:.4f}  median={s['median_flip']:.4f}  sd={s['sd_flip']:.4f}  >0:{s['n_flip_pos']}/{s['n']}")
print()

print("By counter kind within random_stable:")
for kind in ("vmcnt", "lgkmcnt"):
    sub = [r for r in stable if r["kind"] == kind]
    if sub:
        ss = population_stats(f"random_stable.{kind} (n={len(sub)})", sub)
        print(f"  {ss['label']:30s}  mean={ss['mean_flip']:.4f}  >0:{ss['n_flip_pos']}/{ss['n']}")
print()

print("By counter kind within boundary:")
for kind in ("vmcnt", "lgkmcnt"):
    sub = [r for r in boundary if r["kind"] == kind]
    if sub:
        ss = population_stats(f"boundary.{kind} (n={len(sub)})", sub)
        print(f"  {ss['label']:30s}  mean={ss['mean_flip']:.4f}  >0:{ss['n_flip_pos']}/{ss['n']}")
print()

print("Pooled divergence rate (total diverged runs / total effective runs):")
for label, group in (("boundary", boundary), ("random_stable", stable)):
    p, d, n, (lo, hi) = population_pooled_rate(group)
    print(f"  {label:15s}  {d}/{n} = {p:.4f}  95% CI [{lo:.4f}, {hi:.4f}]")
print()

print("Top mutants by flip_rate:")
ranked = sorted(rows, key=lambda r: -r["flip_rate_f"])
for r in ranked[:10]:
    print(f"  {r['population']:13s}  {r['kind']:7s}  {r['kernel']}__L{r['waitcnt_line']}  flip={r['flip_rate_f']:.3f}  ({r['n_diverged']}/{r['n_eff']})")
print()

# Adjusted long-run divergence rate
# Headline: 24.4% of BM-tested mutants diverge (283/1162).
# We sampled the matched population (n=40 stable). Mean flip rate F estimates the
# expected long-run divergence rate within the matched population.
F_stable = s_stable["mean_flip"]
adjusted = 0.244 + F_stable * 0.756
# Bound: pooled rate over matched-population runs
p_pool, d_pool, n_pool, (lo_pool, hi_pool) = population_pooled_rate(stable)
# Wilson 95% on the matched-population per-run divergence rate
adj_lo = 0.244 + lo_pool * 0.756
adj_hi = 0.244 + hi_pool * 0.756

print("Adjusted long-run divergence rate:")
print(f"  baseline single-run rate                : 24.4% (283/1162)")
print(f"  matched-population mean flip (sample)   : F = {F_stable:.4f}")
print(f"  matched-population pooled rate (sample) : {p_pool:.4f}  95% CI [{lo_pool:.4f}, {hi_pool:.4f}]  ({d_pool}/{n_pool})")
print(f"  adjusted long-run divergence (point)    : 24.4% + ({F_stable:.4f} × 75.6%) = {adjusted*100:.2f}%")
print(f"  adjusted long-run divergence (CI band)  : [{adj_lo*100:.2f}%, {adj_hi*100:.2f}%]")
print(f"  (CI derived from per-run Wilson on the 40-mutant sample;")
print(f"   does not account for between-mutant variability.)")
print()

# Save summary csv
with (OUT / "summary.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["statistic", "value"])
    w.writerow(["n_boundary", len(boundary)])
    w.writerow(["n_random_stable", len(stable)])
    w.writerow(["boundary_mean_flip", f"{s_boundary['mean_flip']:.6f}"])
    w.writerow(["boundary_n_flip_pos", s_boundary["n_flip_pos"]])
    w.writerow(["random_stable_mean_flip", f"{s_stable['mean_flip']:.6f}"])
    w.writerow(["random_stable_n_flip_pos", s_stable["n_flip_pos"]])
    w.writerow(["random_stable_pooled_rate", f"{p_pool:.6f}"])
    w.writerow(["random_stable_pooled_ci_lo", f"{lo_pool:.6f}"])
    w.writerow(["random_stable_pooled_ci_hi", f"{hi_pool:.6f}"])
    w.writerow(["adjusted_long_run_divergence_point", f"{adjusted:.6f}"])
    w.writerow(["adjusted_long_run_divergence_ci_lo", f"{adj_lo:.6f}"])
    w.writerow(["adjusted_long_run_divergence_ci_hi", f"{adj_hi:.6f}"])

print(f"summary saved: {OUT/'summary.csv'}")

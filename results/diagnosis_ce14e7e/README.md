# Part 0 diagnosis — silicon-hazard vs cross-launch carryover

**Commit**: `ce14e7e`. **Date**: 2026-05-13.

Run at N=20 on two mutants of `accum_add_16` (BM-match L80, BM-divergent
L85) under five harness variants. Question: are the 20 distinct mutant
dump hashes seen for L85 at N=20 a true silicon hazard, or evidence of
cross-launch state carryover (VGPR file, L1/L2, dispatcher) that would
make the headline divergence-rate statistic unsupportable?

## Variants

- **baseline** — production `tests/mutation/bm_launcher`, original and
  mutant interleaved one-for-one across iterations. Each launch is its
  own subprocess (fresh HIP context).
- **B sleep** — baseline + `time.sleep(0.1)` host-side delay before each
  launcher invocation. Tests whether queue-drain time matters.
- **C reset** — `tests/mutation/_diag/bm_launcher_reset` (clone of the
  production launcher with `hipDeviceReset()` called at process entry).
  Tests whether a heavyweight device reset closes the entropy.
- **D back-to-back** — production launcher, 20 mutant launches with no
  intervening original launch. Tightest cadence; maximum carryover
  surface if any exists.
- **E scrub** — `tests/mutation/_diag/bm_launcher_scrub`. Production
  launcher + (i) `hipMemset(0)` of the non-patterned trailing region of
  every live device allocation after the patterned H2D copy; (ii) load
  and launch `warmup_zero.co` before the user kernel. The warmup is a
  32-VGPR kernel whose first instruction is `s_waitcnt vmcnt(0)
  lgkmcnt(0)` followed by `s_waitcnt_vscnt null, 0` to drain any
  in-flight VMEM/LGKM/VS transactions left over from the previous
  launch, then `v_mov_b32 v0..v31, 0` to zero its register window.

## Schema

`diagnosis.csv` — exactly 10 rows (2 mutants × 5 variants):

```
mutant, variant, n_distinct, mean_launch_ms, max_launch_ms,
median_divergent_lanes, projected_full_sweep_walltime_hours
```

`projected_full_sweep_walltime_hours = mean_launch_ms * 232_400 / 3.6e6`
— mutant launches only at N=100 across the 1162-mutant corpus. Original
overhead is tracked separately.

## Outcome

L80 stays at `n_distinct = 1` under every variant (including D); L85
stays at `n_distinct = 20` under every variant including C and E.
Neither sleep, full `hipDeviceReset`, nor the lightweight scrub closes
the entropy. The L85 hashes are a genuine high-entropy silicon hazard:
the deleted `vmcnt` makes the read of `v5` race a still-in-flight VMEM
load, and each lane snapshots a different completion state on each
launch. Branch: `ALL_HAZARD`. The production harness needs no scrubbing
fix.

## Verifying that variant C actually calls hipDeviceReset

The subprocess walltime numbers above showed baseline 138.6 ms vs C
138.4 ms — a difference within noise. That could mean either the call
is a no-op or the per-process HIP context teardown already does the
work implicitly. To disambiguate, `bm_launcher_reset.cpp` was
instrumented with `std::chrono::steady_clock` around the
`hipDeviceReset()` call itself. Five invocations gave 32.1, 23.0,
22.9, 22.3, 22.6 ms (mean 24.6, after-first 22.7). The call is real,
not a no-op; the cost is just absorbed by the ~138 ms process spawn +
HIP context init + buffer alloc + module load + launch that dominates
the subprocess walltime. Projected cost if ever needed in the
production sweep: ~23 ms × 232,400 = ~89 minutes added — non-trivial
but tolerable inside the 12–14 h budget. Not adopting it for CHECK 2
because Part 0 showed scrubbing has no observable effect on L85's
entropy.

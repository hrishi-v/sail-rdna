# Multi-iteration BM run-to-run variability

Commit baseline: `ce14e7e`. Date: 2026-05-13.

## Question

Single-run BM oracle says 24.4% of mutants diverge (283/1162) and 75.6% match.
The May 1 → May 12 refresh showed 22 verdict flips (11 match→divergent, 11
the reverse). Are matched mutants deterministically tolerated, or probabilistically?

## Design

Two populations sampled from the May 12 BM oracle:

1. **boundary** (n=11): all mutants that flipped match→divergent between
   `results/refresh_db3a40e/baseline_may1/` and `results/refresh_db3a40e/bm/`.
   Counter mix: 8 vmcnt, 3 lgkmcnt.
2. **random_stable** (n=40): random stratified sample of mutants whose verdict
   was match on both dates, proportional to the counter mix of the stable-match
   pool (867 mutants: 95.5% vmcnt, 4.5% lgkmcnt → 38 vmcnt, 2 lgkmcnt).
   Seed 0xC0FFEE.

Each mutant was executed on bare metal **100 times**. On each iteration we
re-ran *both* the original and mutant `.co` to capture nondeterminism on either
side, then diffed register dumps using the same `_diff_dumps` comparator as the
canonical pipeline (`tests/mutation/run_bare_metal.py`). Total: 5,100 mutant
launches + 5,100 original launches (1,409 s wall-clock).

## Per-population results

| Population             | n   | mean flip rate | median | sd     | # with flip>0 |
| ---------------------- | --- | -------------- | ------ | ------ | ------------- |
| boundary               | 11  | 0.5491         | 0.480  | 0.339  | 11/11         |
| random_stable          | 40  | 0.0178         | 0.000  | 0.103  | 3/40          |
| └ random_stable.vmcnt  | 38  | 0.0187         | —      | —      | 3/38          |
| └ random_stable.lgkmcnt| 2   | 0.0000         | —      | —      | 0/2           |
| └ boundary.vmcnt       | 8   | 0.3812         | —      | —      | 8/8           |
| └ boundary.lgkmcnt     | 3   | 0.9967         | —      | —      | 3/3           |

Pooled per-run divergence (total diverged runs / total effective runs):

- boundary:      604 / 1100 = 0.5491, 95% CI [0.5196, 0.5783]
- random_stable: 71 / 4000  = 0.0177, 95% CI [0.0141, 0.0223]

## Top 5 mutants by flip rate

| Rank | Pop           | Kind    | Mutant                       | flip   | n_div/n |
| ---- | ------------- | ------- | ---------------------------- | ------ | ------- |
| 1    | boundary      | lgkmcnt | accum_or_64 L253             | 1.000  | 100/100 |
| 2    | boundary      | lgkmcnt | accum_xor_64 L253            | 1.000  | 100/100 |
| 3    | boundary      | lgkmcnt | accum_sub_64 L253            | 0.990  | 99/100  |
| 4    | boundary      | vmcnt   | loop_accum_add_32 L90        | 0.690  | 69/100  |
| 5    | boundary      | vmcnt   | loop_accum_add_32 L62        | 0.680  | 68/100  |

Notable: one **random_stable** mutant — `loop_accum_xor_32 L62` — has flip rate
0.660 (66/100). The May 12 single-run oracle classified it as matched; over 100
runs it is in fact mostly divergent. This is direct evidence that the matched
population contains misclassified-as-tolerant cases.

## Adjusted long-run divergence rate

Single-run BM divergence rate: 24.4% (283/1162).

Let F be the long-run mean per-run divergence rate within the matched
population. From the stable-match sample, F ≈ 0.0178 with Wilson 95% CI on the
per-run pool [0.0141, 0.0223].

Adjusted long-run divergence rate ≈ 24.4% + F × 75.6%:

- point estimate: **25.74%**
- per-run CI band (does not capture between-mutant variability): [25.47%, 26.09%]

### Caveats

- The CI is derived from the per-run pool over 40 sampled mutants and treats
  each run as independent. It does **not** account for the much larger
  between-mutant variability (most mutants have flip rate 0; a handful drive
  the mean). A bootstrap over mutants would give a wider, more honest band but
  was not run.
- The sample is small (n=40 from 867 stable-match mutants ≈ 4.6%). The 3
  mutants with flip>0 are a thin signal; the true matched-population mean
  could plausibly sit anywhere in the low single digits.
- The boundary set was sampled in full (n=11/11), so its mean is exact for that
  cohort and not an estimate of any broader population.
- We did not measure nondeterminism in the original (unmutated) program. Each
  iteration re-ran the original alongside the mutant, so any orig-side flips
  would have shown up as diffs even when the mutant itself was deterministic.

## Implications

- Tolerance is partially probabilistic, not binary. The 22 May 1 → May 12 flips
  are not noise: every one of the 11 boundary mutants has a flip rate >0, and
  most are in the 30–100% range.
- The matched-mutant population is not deterministically tolerant either: in
  our 40-mutant sample, 3 (7.5%) had flip rate >0, and one had flip rate 0.66.
- Headline 24.4% divergence is therefore a lower bound on the true long-run
  rate; a single re-run sample puts the point estimate at 25.7%.

## Files

- `sample_plan.json` — the 51 (kernel, line) pairs run.
- `per_run.csv` — 5,100 rows, one per (mutant × iteration).
- `per_mutant.csv` — 51 rows with `n_runs`, `n_matched`, `n_diverged`, `flip_rate`.
- `summary.csv` — headline statistics.
- `run.log` — full run console output.
- `run_multi_iter.py`, `summarise.py` — scripts (also in `$CLAUDE_JOB_DIR`).

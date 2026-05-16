## Table 8.1 (replacement) — single-shot vs multi-run

| Stage                 | single-shot | multi-run |
|----------------------|------------:|----------:|
| Mutants in selection | 51 | 51 |
| BM-tested            | 51 | 51 |
| ↳ BM-divergent       | 11  | 15  |
| ↳ BM-match           | 40  | 36  |
| BM-skip              | 0  | 0  |

## Per-counter breakdown (multi-run)

| Counter | total | BM-tested | BM-divergent | BM-match | BM-skip | div_rate |
|---------|------:|----------:|-------------:|---------:|--------:|---------:|
| lgkmcnt |     5 |         5 |            3 |        2 |       0 |    60.0% |
| vmcnt   |    46 |        46 |           12 |       34 |       0 |    26.1% |

## Bucketed flip-rate distribution (buckets = 0,0.10,0.90,1.0)

| Bucket | lgkmcnt | vmcnt |
|---|---|---|
| 0 | 2 | 34 |
| (0, 0.1] | 0 | 3 |
| (0.1, 0.9] | 0 | 7 |
| (0.9, 1] | 3 | 2 |

## 2×2 redundancy overlap (multi-run × §8.3.3 classification)

|  | §8.3.3: redundant (counter zero) | §8.3.3: load-bearing (counter non-zero) | row total |
|---|---:|---:|---:|
| **multi-run never diverges** | 0 (genuinely redundant) | 36 (eager-execution candidate) | 36 |
| **multi-run sometimes diverges** | 0 (oracle correct, §8.3.3 misclassified) | 15 (oracle correct, load-bearing) | 15 |
| **column total** | 0 | 51 | 51 |

## Clean-N split among multi-run never-divergent mutants (threshold n_completed ≥ 0.95 × n_attempted)

| Bucket | count | % of never-divergent |
|---|---:|---:|
| Genuinely silicon-tolerant | 36 | 100.0% |
| Denominator inflated by launcher failures | 0 | 0.0% |
| **Total never-divergent** | 36 | 100.0% |

## Lane-count distribution among diverging runs (scalar-vector asymmetry)

| Counter | n_diverge runs | median lanes | IQR | max |
|---|---:|---:|---:|---:|
| lgkmcnt |            300 |           32 | [32, 32] |  32 |
| vmcnt   |            552 |           31 | [0, 32] |  32 |

## Pilot-replay gate (CHECK 2)

- Overlapping mutants compared        : 51
- Spearman ρ(pilot flip, replay frac) : 0.907
- Max absolute drift                  : 97.0 pp   (worst: deep_chain_64 L168)
- Gate: |drift| ≤ 15 pp on every mutant: FAIL
- Gate: Spearman ρ ≥ 0.9              : PASS

### Top 10 drift rows
| kernel | line | pilot | replay | |Δ| pp |
|---|---:|---:|---:|---:|
| deep_chain_64 | 168 | 0.020 | 0.990 | 97.0 |
| deep_chain_32 | 169 | 0.050 | 0.980 | 93.0 |
| loop_accum_add_32 | 90 | 0.690 | 0.500 | 19.0 |
| loop_accum_add_32 | 60 | 0.480 | 0.630 | 15.0 |
| loop_accum_add_16 | 49 | 0.370 | 0.270 | 10.0 |
| loop_accum_add_32 | 62 | 0.680 | 0.770 | 9.0 |
| loop_accum_xor_32 | 80 | 0.410 | 0.320 | 9.0 |
| loop_accum_add_64 | 163 | 0.040 | 0.010 | 3.0 |
| loop_accum_xor_32 | 82 | 0.350 | 0.370 | 2.0 |
| loop_accum_add_64 | 166 | 0.000 | 0.020 | 2.0 |

## Flip-rate vs distinct wrong dumps (CHECK 2)

- N mutants                            : 51
- Pearson r(flip_rate, n_distinct_mut_dumps_excl_orig_set)  : 0.548
- Spearman ρ                           : 0.959

Question: do high-flip-rate mutants also produce a wider set of
distinct wrong values? r near 1 ⇒ yes; r near 0 ⇒ no, they keep
producing the same wrong answer probabilistically.

### Full scatter rows
| kernel | line | kind | flip_rate | n_distinct_wrong |
|---|---:|---|---:|---:|
| accum_or_64 | 253 | lgkmcnt | 1.000 | 1 |
| accum_sub_64 | 253 | lgkmcnt | 1.000 | 1 |
| accum_xor_64 | 253 | lgkmcnt | 1.000 | 1 |
| deep_chain_64 | 168 | vmcnt | 0.990 | 1 |
| deep_chain_32 | 169 | vmcnt | 0.980 | 30 |
| loop_accum_add_32 | 62 | vmcnt | 0.770 | 50 |
| loop_accum_xor_32 | 62 | vmcnt | 0.650 | 43 |
| loop_accum_add_32 | 60 | vmcnt | 0.630 | 55 |
| loop_accum_add_32 | 90 | vmcnt | 0.500 | 26 |
| loop_accum_xor_32 | 82 | vmcnt | 0.370 | 19 |
| loop_accum_xor_32 | 80 | vmcnt | 0.320 | 32 |
| loop_accum_add_16 | 49 | vmcnt | 0.270 | 19 |
| loop_accum_add_64 | 166 | vmcnt | 0.020 | 2 |
| accum_add_32 | 157 | vmcnt | 0.010 | 1 |
| loop_accum_add_64 | 163 | vmcnt | 0.010 | 1 |
| accum_add_96 | 432 | vmcnt | 0.000 | 0 |
| accum_and_16 | 110 | vmcnt | 0.000 | 0 |
| accum_and_32 | 164 | vmcnt | 0.000 | 0 |
| accum_and_32 | 182 | vmcnt | 0.000 | 0 |
| accum_and_4 | 44 | vmcnt | 0.000 | 0 |
| accum_and_64 | 323 | vmcnt | 0.000 | 0 |
| accum_and_64 | 345 | vmcnt | 0.000 | 0 |
| accum_and_64 | 375 | vmcnt | 0.000 | 0 |
| accum_and_64 | 420 | vmcnt | 0.000 | 0 |
| accum_and_8 | 63 | vmcnt | 0.000 | 0 |
| accum_and_96 | 478 | vmcnt | 0.000 | 0 |
| accum_or_16 | 95 | vmcnt | 0.000 | 0 |
| accum_or_32 | 147 | vmcnt | 0.000 | 0 |
| accum_or_64 | 295 | vmcnt | 0.000 | 0 |
| accum_or_64 | 330 | vmcnt | 0.000 | 0 |
| accum_or_64 | 337 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 265 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 307 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 310 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 320 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 322 | vmcnt | 0.000 | 0 |
| accum_sub_64 | 335 | vmcnt | 0.000 | 0 |
| accum_sub_96 | 151 | lgkmcnt | 0.000 | 0 |
| accum_sub_96 | 477 | vmcnt | 0.000 | 0 |
| accum_xor_96 | 410 | vmcnt | 0.000 | 0 |
| load_compute_store_4 | 41 | lgkmcnt | 0.000 | 0 |
| loop_accum_add_128 | 273 | vmcnt | 0.000 | 0 |
| loop_accum_add_64 | 123 | vmcnt | 0.000 | 0 |
| loop_accum_xor_128 | 238 | vmcnt | 0.000 | 0 |
| loop_accum_xor_128 | 281 | vmcnt | 0.000 | 0 |
| loop_accum_xor_128 | 286 | vmcnt | 0.000 | 0 |
| regs_pressure_32 | 99 | vmcnt | 0.000 | 0 |
| regs_pressure_64 | 136 | vmcnt | 0.000 | 0 |
| regs_pressure_64 | 151 | vmcnt | 0.000 | 0 |
| regs_pressure_64 | 166 | vmcnt | 0.000 | 0 |
| regs_pressure_64 | 216 | vmcnt | 0.000 | 0 |

## Mutants with ≥2 distinct wrong dumps

Count: 9. Written to `previously_unseen_dumps.csv`.

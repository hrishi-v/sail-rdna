# Chapter 8 Dataset Refresh — `db3a40e` vs `2026-05-01`

**Evaluation commit**: `db3a40ee187cd3bba27684073732aa1f845f8f24`
**Refresh date**: 2026-05-12
**Baseline date**: 2026-05-01 (raw artefacts: `tests/mutation/{mutation_results,bare_metal_diff}.csv` mtime 2026-05-01)

## Corpus inventory

| Item | May 1 baseline | Refresh | Note |
|---|---|---|---|
| `_mutant_*.elf` on disk | (not snapshotted) | 1269 | 2 extra `rmw_and_c0xDEAD__L{15,26}` — fuzzer `compile==ok && sail==ok` set excludes them, so not in canonical 1267 |
| Canonical mutants (in `mutation_results.csv`) | 1267 | 1267 | identical key set |
| `_orig_*.elf` | 113 | 113 | |
| Sail-ok originals scored | 112 | 112 | one excluded — same exclusion holds; not material |

## Funnel

| Stage | May 1 | Refresh | Δ |
|---|---:|---:|---:|
| Mutants generated | 1267 | 1267 | 0 |
| BM-tested (launcher succeeded) | 1159 | 1162 | +3 |
| ↳ BM-divergent | 276 | 283 | +7 |
| ↳ BM-match | 883 | 879 | −4 |
| BM-skip (launcher failed) | 108 | 105 | −3 |

## Oracle confusion matrix (over BM-tested subset)

| Cell | May 1 | Refresh | Δ |
|---|---:|---:|---:|
| TP (oracle flag ∧ BM diverge) | 276 | 283 | +7 |
| FP (oracle flag ∧ BM match) | 883 | 879 | −4 |
| FN (no flag ∧ BM diverge) | 0 | 0 | 0 |
| TN (no flag ∧ BM match) | 0 | 0 | 0 |
| Precision = TP/(TP+FP) | 0.2381 (276/1159) | 0.2435 (283/1162) | +0.5pp |
| Recall = TP/(TP+FN) | 1.0000 (276/276) | 1.0000 (283/283) | 0 |
| False-alarm rate on unmodified originals | 0/112 | 0/112 | 0 |

By construction every mutant deletes one waitcnt, so the oracle is expected to flag all 1267; recall = 1.0 in both runs. There is no TN row because no mutant is flag-free.

## Redundancy on BM-match (Q: is the deleted waitcnt redundant?)

| Population | May 1 | Refresh |
|---|---|---|
| BM-match — redundant | 0 / 883 | 0 / 879 |
| BM-match — load-bearing | 883 / 883 | 879 / 879 |
| BM-divergent — redundant (consistency check) | 0 / 276 | 0 / 283 |
| BM-divergent — load-bearing | 276 / 276 | 283 / 283 |

Headline: zero redundant deletions across the entire BM-tested set — every waitcnt the compiler emitted was load-bearing at the moment of its deletion. Result holds.

## Counter-class breakdown

| Counter | Field | May 1 | Refresh | Δ |
|---|---|---:|---:|---:|
| lgkmcnt | total mutants | 195 | 195 | 0 |
| lgkmcnt | BM-tested | 121 | 117 | −4 |
| lgkmcnt | BM-divergent | 74 | 76 | +2 |
| lgkmcnt | divergence rate | **61.2%** | **65.0%** | **+3.8pp ⚠** |
| vmcnt   | total mutants | 1072 | 1072 | 0 |
| vmcnt   | BM-tested | 1038 | 1045 | +7 |
| vmcnt   | BM-divergent | 202 | 207 | +5 |
| vmcnt   | divergence rate | **19.5%** | **19.8%** | +0.3pp |

No vscnt mutants are in this corpus (single-counter waitcnts only; see also `counter_breakdown.csv`).

The lgkmcnt move is just above the 3pp flag threshold. Underlying: 4 fewer mutants succeed at the launcher (skip increased) and 2 more diverge among those that did succeed. On N=117 a single mutant flipping = 0.85pp, so the move is ≈5 mutants. Within noise for silicon re-runs.

## Family breakdown — well-powered families

| Family | Counter | May 1 rate | Refresh rate | Δ |
|---|---|---:|---:|---:|
| accum_n_distinct | lgkmcnt | 13.0% (6/46) | 21.4% (9/42) | +8.4pp ⚠ |
| accum_n_distinct | vmcnt   | 3.7% (22/597) | 3.2% (19/597) | −0.5pp |
| loop_accum       | lgkmcnt | 100% (10/10) | 100% (10/10) | 0 |
| loop_accum       | vmcnt   | 9.6% (18/188) | 10.6% (20/188) | +1.1pp |

Within both well-powered families lgkmcnt divergence ≫ vmcnt: ratio is 6.7× in accum_n_distinct (was 3.5× on May 1) and 9.4× in loop_accum (was 10×). The "lgkmcnt diverges roughly 2× more than vmcnt within well-powered families" claim holds — in fact comfortably.

## Diagnosis

**Sail side is perfectly stable.** The full per-mutant verdict diff between the May 1 `mutation_results.csv` and the refresh is zero rows: every one of the 1267 mutants produces the same `(waitcnt_kind, new_hazard_detected)` verdict and the same hazard message tally. The intervening commits (`cd541b7` — 8 integer/control opcodes for LLVM AMDGPU output; `f0c9a9d` — inline-literal PC bump fix; `19c14ae` — VOP2 imm PC bump fix; `b48d76b` — `check_sgpr_plq` gate on `IN_EXECUTE`; `589a01a` — `plq_push` extract; etc.) touched decode and hazard machinery, but none of those paths exercise the synthetic fuzzer corpus, so verdicts are preserved bit-for-bit. The 2 new `rmw_and_c0xDEAD__L{15,26}` ELFs that appear on disk since May 1 are *not* in the canonical 1267 set (the fuzzer's `sail==ok` flag still excludes that kernel today). The "Fix 1 affecting the two rmw_and_c0xDEAD rows" angle therefore does *not* yet shift the canonical numbers — the change widens the prospective corpus but the canonical 1267 is the same key set.

**BM side moved by 37 verdicts (~3% of mutants).** All deltas above are downstream of this. The breakdown is: 11 yes→no, 11 no→yes, 8 skip→no, 5 yes→skip, 1 skip→yes, 1 no→skip. The yes↔no symmetry (11/11) and the skip churn (15 mutants shift in/out of skip) point at hardware-side run-to-run noise — `regs_pressure`, `accum_*`, `loop_accum_*` and `deep_chain` kernels all read uninitialised regions whose contents depend on driver/HIP state at launch. None of these silicon flips affect the headline statements:

- Recall is still 1.0 (no oracle gap).
- False-alarm on unmodified originals is still 0/112.
- Redundancy on BM-match is still 0.
- Within well-powered families lgkmcnt divergence ≫ vmcnt.

Only one cell in the comparison table moves more than 3pp (lgkmcnt aggregate divergence, +3.8pp) and one well-powered family cell moves more than 1pp (accum_n_distinct lgkmcnt, +8.4pp on N=42). Both are tiny absolute shifts amplified by small denominators. No structural change in the dataset.

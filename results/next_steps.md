● 1. What the implementation does today

  Instruction coverage (per AST + execute dispatch)

  64 opcodes in spec/rdna3_ast.sail, all wired to executes in
  spec/execute/rdna3_execute.sail. Grouped:

  - SOP2 (6): s_add_u32, s_sub_u32, s_and_b32, s_cselect_b32, s_lshr_b64,
  s_and_not1_b32 — full semantics including SCC.
  - SOP1 (3): s_mov_b32, s_mov_b64, s_and_saveexec_b32 — full semantics, EXEC +
  SCC handled.
  - SOPC (3): s_cmp_eq_i32, s_cmp_lg_i32, s_bitcmp0_b32 — full.
  - SOPP (8): s_nop/s_clause/s_delay_alu are no-ops (semantically irrelevant).
  s_endpgm is a hazard-check + halt. s_branch real. s_cbranch_scc1 is a stub
  returning unit — branch not actually taken; control-flow tests rely on linear
  fallthrough. s_sendmsg only checks the MSG_DEALLOC_VGPRS hazard. s_waitcnt
  drains VLQ + PLQ + DS_PENDING; partial drains supported.
  - SOPK (1): s_waitcnt_vscnt — full.
  - VOP1 (1): v_mov_b32 — EXEC-masked, full.
  - VOP2/VOP3 ALU (~22): v_and/or/xor/mov, v_add_nc_u32, v_sub_nc_u32,
  v_lshlrev_b32/b64, v_lshl_add_u32, v_ashrrev_i32, v_mul_lo_u32, v_mul_u32_u24,
   v_xor3_b32, v_or3_b32, v_add3_u32, v_xad_u32, v_mbcnt_lo_u32_b32,
  v_cndmask_b32(_vop3), v_add_co_u32, v_add_co_ci_u32(_vop3), v_mad_u64_u32,
  v_cmp_lt_u32, v_cmp_gt_i32 — all per-lane EXEC-masked, full ALU semantics.
  v_writelane_b32 is broadcast (not lane-targeted), v_readlane_b32 always reads
  lane 0 — both flagged in source as stubbed.
  - SMEM (4): s_load_b32/b64/b128/b256 — read memory, push to PLQ, bump LGKMCNT.
   Drain on s_waitcnt lgkmcnt.
  - FLAT (4): flat_load_b32/b64, flat_store_b32/b64 — full address calc,
  LDS-vs-VMEM split via SHARED_BASE/LIMIT, VLQ for loads, VSCNT for stores.
  - GLOBAL (2): global_load_b32, global_store_b32 — full, both saddr=null and
  SGPR+VGPR forms; loads stage to VLQ.
  - DS (1): ds_read_b32 only. Full semantics + bank-conflict diagnostic.
  ds_write_b32 not implemented at all.
  - MUBUF (1): buffer_load_b128 only (4 VMCNT credits). Other MUBUF variants
  absent.
  - SCRATCH (4): scratch_load_b32/b64, scratch_store_b32/b64 — all four are pure
   counter bumps; no memory effect, no address calc. Source confirms.
  Effectively unimplemented except for hazard accounting.

  Absent but exercised by the corpus

  From tests/generated/instruction_frequency.csv (frequencies after dedup):
  ds_load_b32 (56 occurrences), ds_store_b32 (3), s_barrier (3), buffer_gl0_inv
  (3), s_movk_i32 (1), v_subrev_nc_u32_e32 (1), v_mad_u32_u24 (3). 12/124 fuzz
  kernels classified unsupported. LLVM also emits DPP/SDWA encodings that the
  decoder rejects when present (not common in this corpus).

  Beyond instruction semantics

  - Counters: VMCNT (7-bit), VSCNT (6-bit), LGKMCNT (6-bit), DS_PENDING (5-bit),
   PLQ_COUNT, VLQ_COUNT.
  - Queues:
    - PLQ (Pending Load Queue, 16 entries × up to 8 dwords) — SMEM loads,
  drained by s_waitcnt lgkmcnt.
    - VLQ (Vector Load Queue, 128 entries × 32 lanes) — defers VGPR writes for
  VMEM loads until s_waitcnt vmcnt(0). Genuinely models the issue-commit gap.
    - VMQ_PENDING (256-bit bitmap) — which VGPRs have in-flight VMEM loads.
  Rebuilt from VLQ on drain.
  - Hazard diagnostics (printed to stdout, prefixed [HAZARD]):
    - Read of VGPR with pending VMEM (check_vgpr_vlq).
    - Read of SGPR with pending SMEM (check_sgpr_plq).
    - s_endpgm with outstanding VMEM/VSCNT.
    - MSG_DEALLOC_VGPRS with VMEM queue non-empty.
    - ds_read_b32 bank conflicts (with cycle-penalty estimate referencing
  tests/experiments/ds_read_b32_latency.py).
  - EXEC: only EXEC_LO (wave32). EXEC-mask gating implemented inside every
  vector op; s_and_saveexec_b32 modifies it correctly.
  - Memory model: unified flat MEM array; LDS sandboxed at LDS_BASE=0x8000;
  SHARED_BASE/LIMIT used to route flat ops to LDS vs VMEM.
  - VCC: stored in SGPR[106..107], read/written by carry-producing/consuming
  ops.

  Explicitly not modeled

  - Multi-wave / multi-CU concurrency — single wavefront only.
  - Atomics (no *_atomic_*).
  - True scratch memory — scratch_* are stubs.
  - Image / sampler ops — entirely absent.
  - DPP / SDWA modifier semantics — decoder doesn't handle these encodings.
  - F16/F32/F64 floating-point — entire FP family absent.
  - s_cbranch_scc0/execz/vccz/... — only scc1 exists in AST and even that's a
  stub.
  - s_barrier and other workgroup-scoped sync.
  - VOPC encoding (only VOP3 form of v_cmp_* is wired).

  Harness components

  1. Sail→C build (Makefile): sail -c lowers the spec to C, linked with
  test_harness/{main.cpp,FlightRecorder.cpp,utils.cpp} into rdna3_emu binary.
  Loads ELF, runs step() until halt, dumps registers.
  2. make test: builds emu + assembles 35 tests/asm/*.asm via clang -target
  amdgcn-amd-amdhsa -mcpu=gfx1101, runs emu against the binary the Makefile
  picks up. Smoke test only; no diffing.
  3. tests/diff/ (pytest): for each manifest, runs Sail emu and bare-metal HIP
  harness, parses dumps, compares VGPRs lane-by-lane plus a "no-clobber"
  allow-list check. ~24 hand-written kernels in scope; baseline run shows
  store_vgpr_reuse failing.
  4. tests/experimental/ (pytest --experimental): same comparison but
  auto-generates manifests from raw .hip files using elf_metadata.py (reads
  .amdgpu_metadata to discover kernarg layout).
  5. tests/fuzzer/ (run_fuzzing.py + generate_kernels.py): 124 generated HIP
  kernels (accum_*, loop_accum_*, store_chain_*, rmw_*, regs_pressure_*,
  deep_chain_*, mixed_loads_*, etc.). Compiles, runs through Sail, classifies.
  Current results: 108 ok/ok, 12 unsupported, 4 sail errors, 12 compile fails.
  Produces tests/generated/instruction_frequency.csv.
  6. tests/mutation/run_mutation.py: deletion-mutation. Removes one waitcnt at a
   time from each Sail-clean kernel, runs Sail, counts new hazard messages. Last
   run: 1103 mutants, 100% detected as having new hazards. Split: 936
  vmcnt-kind, 167 lgkmcnt-kind. Produces mutation_results.csv +
  bare_metal_diff.csv.
  7. tests/experiments/: stand-alone microbenchmarks against bare metal —
  s_load_b{32,64,128}_latency, s_load_b128_unaligned, smem_cache_sweep,
  smem_latency_thrash, ds_read_b32_latency, timer_calibration. Plus
  waitcnt_corpus_stats.py (already produced summary CSV: vmcnt(0)=1718,
  vmcnt(N>0) heavy tail to 62, lgkmcnt(0)=1547 with tiny tail, vscnt(0)=1449).
  8. fuzzer/ (separate, older): asm-level pytest fuzzer with ~150 generated .asm
   files. Less integrated than tests/fuzzer/.
  9. bare_metal_test/: ROCm/HIP host harness; produces register dumps consumed
  by the diff layer.

  2. Core contribution as the code reflects it

  A clone-and-run reader sees: a Sail spec covering ~64 RDNA3 opcodes — enough
  VOP, SMEM, FLAT, GLOBAL, and one each of DS/MUBUF to run real LLVM-generated
  HIP kernels — paired with a bare-metal differential harness on an RX 7800XT
  and a hazard-instrumented executable model. The most distinctive piece of
  engineering in the spec is not the ALU semantics (those are mechanical) but
  the explicit modeling of the issue-commit pipeline for memory: a VLQ that
  defers VGPR writes until s_waitcnt vmcnt(0), a PLQ for SMEM, VMQ_PENDING
  bitmap, and stale-read diagnostics. The mutation harness then weaponises the
  spec as a lint for missing waitcnts: deleting any waitcnt in 1103 sites across
   108 generated kernels produces a hazard message 100% of the time. Read
  together, the repo is best described as "a Sail spec of RDNA3 memory ordering,
   used as a static-style checker for waitcnt correctness, validated by
  differential testing on real silicon", not as a general-purpose RDNA3
  simulator. The ALU coverage is a means to running enough real code for the
  ordering claims to bite.

  3. Small experiments

  Effort estimates assume you, working alone, with the existing harness running.

  #: A
  Experiment: Re-run mutation harness with all kernels' diff vs bare metal
    recorded (already partially in bare_metal_diff.csv). Cross-tabulate: (hazard

    fired) × (bare-metal diverged) to produce confusion matrix.
  Effort: 1–4 h
  Artefact: One 2×2 table + per-kind breakdown
  What it lets you say: "Of N detected hazards, M actually corrupt bare-metal
    output; the spec's lint precision is X%" — currently you only have detection

    rate, not precision.
  Touches: Analysis only
  ────────────────────────────────────────
  #: B
  Experiment: Histogram + plot of waitcnt-N immediates from
    waitcnt_corpus_summary.csv already produced. Long-tail visualisation per
    counter.
  Effort: <1 h
  Artefact: One graph + 200-word caption
  What it lets you say: Quantifies how often LLVM emits partial-drain waitcnts
  vs
    full-drain — motivates the partial-wait model in the spec.
  Touches: Analysis only
  ────────────────────────────────────────
  #: C
  Experiment: Add [DIAG] line to every hazard print recording (PC, VGPR, vmcnt,
    vscnt, lgkmcnt) and replay mutation harness. Rank kernels by hazard density.
  Effort: 1–4 h
  Artefact: New CSV columns + a "top 10 most hazard-dense kernels" table
  What it lets you say: "The spec catches hazards at the granularity of
    individual register/cycle pairs, not just per-kernel" — concrete diagnostic
    story.
  Touches: Spec (print only) + analysis
  ────────────────────────────────────────
  #: D
  Experiment: Extend mutation harness to flip, not delete: change vmcnt(0) →
    vmcnt(N) for N ∈ {1,2,4,8,16,32,63}. Same detection metric. (See detailed
    assessment below.)
  Effort: 4–8 h
  Artefact: New CSV; per-N detection rate; per-site max safe N
  What it lets you say: "Beyond all-or-nothing, the spec catches partial-drain
    weakening at granularity X" — graduated lint claim.
  Touches: Harness only
  ────────────────────────────────────────
  #: E
  Experiment: Run differential test suite under three Sail builds: stock, with
    VLQ disabled, with VMQ_PENDING disabled. Count regressions.
  Effort: 1–4 h
  Artefact: One table: feature × tests passing
  What it lets you say: "Each piece of the memory model is load-bearing —
    disabling VLQ regresses N tests, disabling VMQ regresses M" — ablation
    evidence for the spec's design.
  Touches: Spec (toggles) + harness
  ────────────────────────────────────────
  #: F
  Experiment: s_cbranch_scc1 audit: grep corpus for branch instructions, count
    occurrences not exercised by tests, document gap.
  Effort: <1 h
  Artefact: One paragraph + small table
  What it lets you say: Honest accounting of what's stubbed; pre-empts an
    examiner question.
  Touches: Analysis only
  ────────────────────────────────────────
  #: G
  Experiment: v_writelane/v_readlane correctness check against bare metal on a
    tiny targeted kernel — confirms the stub is wrong, quantifies how wrong.
  Effort: 1–4 h
  Artefact: One test result row, possibly a known-divergence entry
  What it lets you say: "Stubbed cross-lane ops; here's exactly what they get
    wrong on real silicon" — turns an embarrassment into a documented
  limitation.
  Touches: Corpus + diff harness
  ────────────────────────────────────────
  #: H
  Experiment: Re-run fuzzer with -O0 and -O3 variants of every kernel (currently

    only -O2). Compare hazard / coverage rates per opt level.
  Effort: 1–4 h
  Artefact: Three result CSVs + a comparison plot
  What it lets you say: "Hazard density depends on optimisation level; the spec
    catches issues across the LLVM opt spectrum" — robustness claim.
  Touches: Corpus driver only

  Specific assessment: waitcnt vmcnt(N) increment mutation (= experiment D)

  Reuse: ~80%. tests/mutation/run_mutation.py already does the heavy lifting —
  kernel selection, asm parsing, finding waitcnt indices, running the emu,
  parsing hazards, classifying detection. The whole mutation loop, setup-file
  management, and CSV output stay.

  What's new:
  1. Replace _write_mutant (currently overwrites the line with ; MUTATED) with a
   function that parses the operand list and produces a family of mutants, one
  per (site, N). The waitcnt operand parser is small — regex on
  vmcnt\(\s*(\d+)\s*\) and a substitution. Maybe 30 LOC.
  2. Adjust the outer loop to iterate (site × N_value) instead of (site);
  current loop produces one row per site, you'll produce ~7×.
  3. Add a per-site-max-safe-N post-pass: for each site, find the largest N at
  which no new hazard fires; that's the column you actually want for the thesis.
  4. Decide what "vscnt" / "lgkmcnt" mutations look like — s_waitcnt_vscnt is a
  separate instruction with a single immediate; s_waitcnt packs
  vmcnt+lgkmcnt+expcnt into one operand list. The parser needs both forms.

  Hidden icebergs:
  - s_waitcnt operand format varies. Sometimes named (vmcnt(0)), sometimes
  packed bare immediate (the corpus_stats script handles both — you'd want to
  lift IMM_RE decoding from tests/experiments/waitcnt_corpus_stats.py).
  Bare-immediate mutation needs careful bit-field surgery.
  - Sites with vmcnt(0) lgkmcnt(0) need a decision: mutate one counter at a
  time, or both? One at a time is right but doubles the grid.
  - The 7-cap on vmcnt immediates in your AST (bits(6) value) means N>62 is
  meaningless; sites where current vmcnt(0) sits behind a load chain of <N
  pending loads will trivially "pass" with N too large. You need to clamp N at
  runtime to min(VMCNT_at_site, requested_N) as observed, which means a first
  pass to record VMCNT-at-site (you'd want a [DIAG] print for that — overlaps
  with experiment C).
  - s_waitcnt semantics in the spec partial-drain: s_waitcnt(simm) already
  correctly drains down to the target rather than to zero, so the spec is ready.
   No spec changes needed.

  Honest estimate: 4–8 hours, not <4. The parser variants (named vs packed) and
  the mixed-counter sites are the time sinks. If you scope to "named-form vmcnt
  only, single counter at a time" you can probably do it in 3 hours with a
  meaningful first cut. Adding lgkmcnt+vscnt and the packed form pushes it to a
  full day.

  What it produces that the deletion mutation doesn't: a graduated claim. Right
  now you can say "the spec detects every removed waitcnt in 1103 sites." With
  this you can say "for each waitcnt site, the spec detects the smallest N at
  which the synchronisation becomes insufficient — median safe-N relaxation is
  X, with Y% of sites tolerating N≥1 before any hazard fires." That's a much
  sharper thesis sentence.

✻ Baked for 3m 52s

※ recap: Goal: pick next direction for Sail RDNA3 thesis with six weeks left. I
  delivered a three-part inventory: implementation status, core contribution as
  code shows it, and 5–8 small experiments. Next: you triage which experiment to
   run. (disable recaps in /config)
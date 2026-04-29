Audit complete. One stub (s_cbranch_scc1), one fully-implemented branch
  (s_branch), all other conditional variants absent from the AST. Corpus
  contains exactly two kernels with branch instructions: s_branch.asm (uses
  unconditional s_branch, fully covered) and llvm_sail_bug.asm (uses
  s_cbranch_scc1, runs only under make test, not in the differential harness).
  Both pass under make test; neither failure mode is attributable to a stub. The
   fuzzer-generated corpus (tests/generated/asm/*.s, 124 kernels) contains zero
  branches — the generator emits straight-line accumulator code only. HIP
  kernels (tests/kernels/*.hip, tests/experimental/*.hip) have no compiled
  branches in the asm path tested.

  Stub status (quoted bodies):

  s_cbranch_scc1 — STUB (rdna3_s_execute.sail:135-139):
  function s_cbranch_scc1 simm = {
      // NOP stub: branch semantics not needed for hazard detection.
      ()
  }
  Decoded (rdna3_s_decode.sail:51, opcode 0b0100010), dispatched
  (rdna3_execute.sail:25), but no PC update and no SCC read — always falls
  through.

  s_branch — FULLY IMPLEMENTED (rdna3_s_execute.sail:183-187):
  function s_branch simm = {
      let offset : QWORD = get_slice_int(64, signed(simm) * 4, 0);
      PC = PC + offset
  }

  All other s_cbranch_* variants (scc0, vccz, vccnz, execz, execnz, cdbgsys*) —
  ABSENT from AST, decoder, and dispatch.

  Corpus occurrences:

  ┌──────────────────┬─────────────┬─────────────────────────────────┐
  │      opcode      │ occurrences │        kernels-affected         │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_branch         │ 1           │ 1 (tests/asm/s_branch.asm)      │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_scc1   │ 1           │ 1 (tests/asm/llvm_sail_bug.asm) │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_scc0   │ 0           │ 0                               │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_vccz   │ 0           │ 0                               │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_vccnz  │ 0           │ 0                               │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_execz  │ 0           │ 0                               │
  ├──────────────────┼─────────────┼─────────────────────────────────┤
  │ s_cbranch_execnz │ 0           │ 0                               │
  └──────────────────┴─────────────┴─────────────────────────────────┘

  Total kernels containing any branch instruction: 2. Of those, 2 pass make
  test. 0 fail. s_branch.asm is also in the differential harness (manifest +
  .inc + allow-list) and passes there; llvm_sail_bug.asm is not in the
  differential harness — no bare-metal cross-check exists, only Sail-side
  execution to halt.

  Step 4 verdict — HOLDS, with caveats:

  The claim as worded ("taken s_cbranch_*") is verified. The only s_cbranch_* in
   the corpus is the one in llvm_sail_bug.asm, and that test's PASS condition
  (EXPECT_ERROR from the s_sendmsg/VSCNT hazard) is satisfied precisely because
  the stub falls through — taking the branch would skip the flat_store_b32 at
  lines 20-24 and prevent the hazard from firing. So no test currently depends
  on the taken path; one test (llvm_sail_bug) actively depends on the
  fallthrough.

  Caveats to note in the limitations text:
  - s_branch.asm does depend on a taken branch, but s_branch is fully
  implemented (unconditional), so it's not a stub-related dependency.
  - llvm_sail_bug.asm is outside the differential harness, so divergence between
   stub-fallthrough and actual hardware (which may take the branch given the
  kernarg-derived SCC) is not observed. Bare-metal behaviour for that kernel is
  unverified — the claim "linear fallthrough produces the same result" is
  unconfirmed for that single kernel.
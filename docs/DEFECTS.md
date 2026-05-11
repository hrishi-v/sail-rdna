# Defects Log

Known inconsistencies and minor bugs deferred for later cleanup. Not blockers.

## Open

### D1 — fuzzer/runner.py target mismatch (gfx1100 vs gfx1101)

- **Location:** `fuzzer/runner.py:13` (clang assemble path uses `-mcpu=gfx1100`)
- **Context:** Same file line 36 uses `--offload-arch=gfx1101` for the hipcc path. Rest of harness (Makefile, tests/diff, tests/experimental, scripts/, tests/experiments/) all on gfx1101.
- **Likely cause:** historical — gfx1101 was reportedly missing ROCm support at some earlier point, so fuzzer was pinned to gfx1100.
- **Impact:** Fuzzer-only. Differential harness path is unaffected. Generated assembly may diverge in edge cases (Navi 31 vs Navi 32), though the core RDNA3 ISA encoding is shared.
- **Discovered:** 2026-05-11 during ROCm-sample coverage audit.
- **Action:** deferred; revisit if fuzzer output ever diverges from bare-metal due to target mismatch.

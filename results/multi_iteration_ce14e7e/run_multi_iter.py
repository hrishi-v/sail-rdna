"""Run sampled BM-match mutants N times each on bare metal.

Reads sample_plan.json (boundary + random_stable_match populations).
For each mutant: ensure orig.co & mutant.co exist (build via clang if missing),
then run launcher N times for BOTH orig and mutant on each iteration so we
capture nondeterminism on either side. Compare register dumps using the same
_diff_dumps logic as the canonical pipeline.

Outputs:
  per_run.csv      one row per iteration
  per_mutant.csv   per-mutant flip_rate, n_runs, n_diverged
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/hrishi/Documents/sail-rdna")
MUT = ROOT / "tests/mutation"
ASM_DIR = ROOT / "tests/generated/asm"
HIP_DIR = ROOT / "tests/fuzzer/generated"
MUT_DIR = MUT / "mutants"
BUILD = MUT / "build_bm"
LAUNCHER = MUT / "bm_launcher"
OUT_DIR = ROOT / "results/multi_iteration_ce14e7e"
PLAN = OUT_DIR / "sample_plan.json"

sys.path.insert(0, str(ROOT / "tests" / "experimental"))
import conftest as exp  # noqa: E402

N_RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 100


def _clang_s_to_co(asm: Path, co: Path) -> None:
    subprocess.run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         str(asm), "-o", str(co)],
        check=True, capture_output=True, timeout=60,
    )


def _clang_s_to_elf(asm: Path, elf: Path) -> None:
    subprocess.run(
        ["clang", "-target", "amdgcn-amd-amdhsa", "-mcpu=gfx1101",
         "-c", str(asm), "-o", str(elf)],
        check=True, capture_output=True, timeout=60,
    )


def _run_launcher(manifest: Path, co: Path, out: Path, timeout: int = 30):
    try:
        p = subprocess.run(
            [str(LAUNCHER), str(manifest), str(co), str(out)],
            capture_output=True, text=True, errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        return 124, f"timeout"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _parse_dump(path: Path):
    out = {}
    if not path.exists():
        return out
    for ln in path.read_text().splitlines():
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        out[k.strip()] = v.split()
    return out


def _diff_dumps(orig, mut):
    diffs = []
    keys = sorted(set(orig.keys()) | set(mut.keys()))
    for k in keys:
        o = orig.get(k, [])
        m = mut.get(k, [])
        if o != m:
            mis = [(l, a, b) for l, (a, b) in enumerate(zip(o, m)) if a != b]
            if mis:
                s = mis[0]
                diffs.append(f"{k} lane{s[0]:02d} orig={s[1]} mut={s[2]} ({len(mis)})")
            else:
                diffs.append(f"{k} length mismatch")
    return diffs


def ensure_kernel_built(kernel: str):
    elf = BUILD / f"{kernel}.elf"
    mf_path = BUILD / f"{kernel}_manifest.json"
    orig_co = BUILD / f"{kernel}_orig.co"
    if elf.exists() and mf_path.exists() and orig_co.exists():
        return mf_path, orig_co
    asm_path = ASM_DIR / f"{kernel}.s"
    hip_path = HIP_DIR / f"{kernel}.hip"
    if not asm_path.exists() or not hip_path.exists():
        raise FileNotFoundError(f"sources missing for {kernel}")
    src = hip_path.read_text()
    kernel_name = exp._parse_kernel_name(src)
    _clang_s_to_elf(asm_path, elf)
    manifest = exp._build_manifest(f"bm_{kernel}", kernel_name, src, elf)
    mf_path.write_text(json.dumps(manifest))
    _clang_s_to_co(asm_path, orig_co)
    return mf_path, orig_co


def ensure_mutant_co(kernel: str, line: int):
    mut_co = BUILD / f"{kernel}__L{line}.co"
    if mut_co.exists():
        return mut_co
    mut_asm = MUT_DIR / f"{kernel}__L{line}.s"
    if not mut_asm.exists():
        raise FileNotFoundError(f"mutant asm missing {mut_asm}")
    _clang_s_to_co(mut_asm, mut_co)
    return mut_co


def run_one(kernel: str, line: int, kind: str, population: str):
    """Returns list of per-run dicts."""
    rows = []
    mf, orig_co = ensure_kernel_built(kernel)
    mut_co = ensure_mutant_co(kernel, line)
    tmp_orig = BUILD / f"_multi_{kernel}_orig.txt"
    tmp_mut = BUILD / f"_multi_{kernel}_L{line}_mut.txt"
    for i in range(N_RUNS):
        rc_o, _ = _run_launcher(mf, orig_co, tmp_orig)
        rc_m, _ = _run_launcher(mf, mut_co, tmp_mut)
        if rc_o != 0 or rc_m != 0 or not tmp_orig.stat().st_size or not tmp_mut.stat().st_size:
            rows.append({
                "kernel": kernel, "waitcnt_line": line, "kind": kind,
                "population": population, "iter": i,
                "rc_orig": rc_o, "rc_mut": rc_m,
                "matched": "skip", "diff_summary": "launcher failure",
            })
            continue
        op = _parse_dump(tmp_orig)
        mp = _parse_dump(tmp_mut)
        diffs = _diff_dumps(op, mp)
        match = len(diffs) == 0
        rows.append({
            "kernel": kernel, "waitcnt_line": line, "kind": kind,
            "population": population, "iter": i,
            "rc_orig": rc_o, "rc_mut": rc_m,
            "matched": "yes" if match else "no",
            "diff_summary": ("" if match else " ; ".join(diffs)[:200]),
        })
    return rows


def main():
    plan = json.loads(PLAN.read_text())
    sample = []
    for r in plan["boundary_match_to_diverge"]:
        sample.append((r["kernel"], r["line"], r["kind"], "boundary"))
    for r in plan["random_stable_match"]:
        sample.append((r["kernel"], r["line"], r["kind"], "random_stable"))

    all_rows = []
    per_mutant = []
    t0 = time.monotonic()
    for idx, (k, l, kk, pop) in enumerate(sample, 1):
        ts = time.monotonic()
        try:
            rs = run_one(k, l, kk, pop)
        except Exception as e:
            print(f"[{idx}/{len(sample)}] {k}__L{l} ERROR: {e}", flush=True)
            per_mutant.append({
                "kernel": k, "waitcnt_line": l, "kind": kk, "population": pop,
                "n_runs": 0, "n_matched": 0, "n_diverged": 0, "n_skip": 0,
                "flip_rate": "",
            })
            continue
        all_rows.extend(rs)
        n_match = sum(1 for r in rs if r["matched"] == "yes")
        n_div = sum(1 for r in rs if r["matched"] == "no")
        n_skip = sum(1 for r in rs if r["matched"] == "skip")
        n_eff = n_match + n_div
        flip = n_div / n_eff if n_eff else 0.0
        per_mutant.append({
            "kernel": k, "waitcnt_line": l, "kind": kk, "population": pop,
            "n_runs": len(rs), "n_matched": n_match, "n_diverged": n_div, "n_skip": n_skip,
            "flip_rate": f"{flip:.4f}",
        })
        dt = time.monotonic() - ts
        print(f"[{idx}/{len(sample)}] {pop:13s} {k}__L{l}  match={n_match}  div={n_div}  skip={n_skip}  flip={flip:.3f}  ({dt:.1f}s)", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "per_run.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kernel", "waitcnt_line", "kind", "population", "iter", "rc_orig", "rc_mut", "matched", "diff_summary"])
        w.writeheader(); w.writerows(all_rows)
    with (OUT_DIR / "per_mutant.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kernel", "waitcnt_line", "kind", "population", "n_runs", "n_matched", "n_diverged", "n_skip", "flip_rate"])
        w.writeheader(); w.writerows(per_mutant)
    print(f"\ntotal {time.monotonic()-t0:.1f}s")


if __name__ == "__main__":
    main()

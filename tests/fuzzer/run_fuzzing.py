from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

FUZZER_DIR = Path(__file__).resolve().parent
REPO_ROOT = FUZZER_DIR.parents[1]
GEN_DIR = FUZZER_DIR / "generated"
RESULTS_CSV = FUZZER_DIR / "results.csv"

ASM_OUT_DIR = REPO_ROOT / "tests" / "generated" / "asm"
FREQ_CSV = REPO_ROOT / "tests" / "generated" / "instruction_frequency.csv"
AST_FILE = REPO_ROOT / "spec" / "rdna3_ast.sail"

sys.path.insert(0, str(REPO_ROOT / "tests" / "experimental"))
import conftest as exp  # noqa: E402

HAZARD_RE = re.compile(r"\[(?:HAZARD|DIAG)\][^\n]*")
UNSUPPORTED_MARKERS = (
    "Unimplemented instruction",
    "Executing invalid instruction",
    "VOP3 Decode Error",
    "Decode Error",
)

# Matches a mnemonic at the start of an asm line (after optional whitespace).
# Rejects directives (.foo), labels (foo:), and comments (; or //).
_ASM_LINE_RE = re.compile(
    r"^\s+([a-z][a-z0-9_]*)\b"
)

# Tokens in Sail AST names that are encoding-form suffixes, not part of the
# AMD mnemonic — strip so e.g. Inst_V_CNDMASK_B32_VOP3 -> v_cndmask_b32.
_AST_SUFFIX_STRIP = ("_VOP3", "_VOP3SD", "_VOPC", "_SOPC", "_SOPK")

# Encoding suffixes emitted by the AMD assembler (not part of the base
# mnemonic). Strip before comparing against the Sail-supported set.
_ASM_SUFFIX_STRIP = ("_e32_dpp", "_e64_dpp", "_e32", "_e64", "_dpp", "_sdwa")


def _normalize_mnemonic(mn: str) -> str:
    for suf in _ASM_SUFFIX_STRIP:
        if mn.endswith(suf):
            return mn[: -len(suf)]
    return mn


def _silent_run(cmd, cwd, label):
    try:
        p = subprocess.run(cmd, cwd=cwd, timeout=120,
                           capture_output=True, text=True)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"{label} timed out after {e.timeout}s") from e
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "")[-400:]
        raise RuntimeError(f"{label} failed (exit {p.returncode}): {tail}")


exp._diff._run = _silent_run


def _ensure_emu() -> Path:
    emu = REPO_ROOT / "rdna3_emu"
    if not emu.exists():
        subprocess.run(["make", "emu"], cwd=REPO_ROOT, check=True)
    return emu


def _run_emu_capture(emu: Path, sail_bin: Path, timeout: int = 60):
    try:
        p = subprocess.run([str(emu), str(sail_bin)], cwd=REPO_ROOT,
                           capture_output=True, text=True, errors="replace",
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return (-1, "", f"timeout after {timeout}s")
    return (p.returncode, p.stdout, p.stderr)


def _cleanup(exp_name: str) -> None:
    sail_bin = REPO_ROOT / "tests" / "bin" / f"{exp_name}.bin"
    setup = exp._diff.SETUP_DIR / f"{exp_name}.setup"
    for p in (sail_bin, setup):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def _load_manifest_meta() -> dict[str, dict]:
    path = GEN_DIR / "manifest.json"
    if not path.exists():
        return {}
    entries = json.loads(path.read_text())
    return {e["name"]: e for e in entries}


def _load_sail_supported_mnemonics() -> set[str]:
    supported: set[str] = set()
    if not AST_FILE.exists():
        return supported
    for m in re.finditer(r"\bInst_([A-Z0-9_]+)\b", AST_FILE.read_text()):
        name = m.group(1)
        if name == "INVALID":
            continue
        for suf in _AST_SUFFIX_STRIP:
            if name.endswith(suf):
                name = name[: -len(suf)]
                break
        supported.add(name.lower())
    return supported


def _parse_asm_mnemonics(asm_path: Path) -> list[str]:
    mnemonics: list[str] = []
    for raw in asm_path.read_text().splitlines():
        line = raw.split(";", 1)[0].split("//", 1)[0]
        if not line.strip():
            continue
        if line.lstrip().startswith("."):
            continue
        if ":" in line and not line.startswith((" ", "\t")):
            continue
        m = _ASM_LINE_RE.match(line)
        if not m:
            continue
        mnemonics.append(m.group(1))
    return mnemonics


def _first_unsupported(asm_path: Path, supported: set[str]) -> str:
    for mn in _parse_asm_mnemonics(asm_path):
        if _normalize_mnemonic(mn) not in supported:
            return mn
    return ""


def run_one(hip_path: Path, do_bare_metal: bool, emu: Path,
            meta_by_name: dict[str, dict],
            supported: set[str]) -> dict:
    src = hip_path.read_text()
    kernel_name = exp._parse_kernel_name(src)
    row = {
        "kernel": hip_path.stem,
        "compile": "",
        "sail": "",
        "hazards": "",
        "unsupported": "",
        "unsupported_inst": "",
        "hip": "n/a",
        "dump": "n/a",
        "notes": "",
    }
    if not kernel_name:
        row["compile"] = "skip"
        row["notes"] = "no __global__ kernel"
        return row

    meta = meta_by_name.get(hip_path.stem, {})
    opt_level = meta.get("opt", "-O1")

    exp_name = f"_fuzz_{hip_path.stem}"
    instrumented_src = exp._inject_dump_hook(src)
    vgprs = exp._detect_vgprs(src)
    capture_prefix = exp._detect_capture_prefix(src)

    try:
        bin_src, elf_path = exp._compile_for_sail(
            instrumented_src, exp_name, kernel_name,
            vgpr_indices=vgprs, capture_prefix=capture_prefix,
            opt_level=opt_level,
        )
    except RuntimeError as e:
        row["compile"] = "fail"
        row["notes"] = str(e)[:300]
        return row
    row["compile"] = "ok"

    # Preserve .s into tests/generated/asm/<kernel>.s
    asm_src = exp.EXP_BUILD_DIR / f"{exp_name}.s"
    asm_dst = ASM_OUT_DIR / f"{hip_path.stem}.s"
    if asm_src.exists():
        ASM_OUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(asm_src, asm_dst)

    try:
        manifest = exp._build_manifest(exp_name, kernel_name, src, elf_path)
    except RuntimeError as e:
        row["sail"] = "skip"
        row["notes"] = f"manifest: {e}"[:300]
        return row

    setup_path = exp._diff.SETUP_DIR / f"{exp_name}.setup"
    exp._write_setup_file(manifest, setup_path)
    sail_bin = REPO_ROOT / "tests" / "bin" / f"{exp_name}.bin"
    shutil.copy(bin_src, sail_bin)

    try:
        rc, out, err = _run_emu_capture(emu, sail_bin)
        blob = (out or "") + (err or "")
        unsupported = [m for m in UNSUPPORTED_MARKERS if m in blob]
        hazards = list(dict.fromkeys(h.strip() for h in HAZARD_RE.findall(blob)))

        if unsupported:
            row["sail"] = "unsupported"
            row["unsupported"] = " | ".join(unsupported)
            if asm_dst.exists():
                row["unsupported_inst"] = _first_unsupported(asm_dst, supported)
        elif rc != 0:
            row["sail"] = "error"
            row["notes"] = f"sail rc={rc}; tail={blob[-200:]}"
        else:
            row["sail"] = "ok"
        row["hazards"] = " | ".join(hazards)

        if do_bare_metal and row["sail"] == "ok":
            try:
                exp._run_hip_experimental(manifest, instrumented_src)
                row["hip"] = "ok"
                sail_vec = (REPO_ROOT / "outputs" / "register_dumps"
                            / f"vec_{exp_name}.log")
                hip_vec = (exp._diff.HIP_OUTPUT_DIR
                           / f"{exp_name}_vector_registers")
                _, _, all_ok = exp._compare_dumps(manifest, sail_vec, hip_vec)
                row["dump"] = "match" if all_ok else "mismatch"
            except RuntimeError as e:
                row["hip"] = "fail"
                row["notes"] = (row["notes"] + f"; hip: {e}")[:300]
        return row
    finally:
        _cleanup(exp_name)


def _aggregate_frequencies(supported: set[str]) -> list[tuple[str, int, str]]:
    counts: Counter[str] = Counter()
    for p in sorted(ASM_OUT_DIR.glob("*.s")):
        counts.update(_parse_asm_mnemonics(p))
    rows = []
    for mn, cnt in counts.most_common():
        base = _normalize_mnemonic(mn)
        rows.append((mn, cnt, "y" if base in supported else "n"))
    FREQ_CSV.parent.mkdir(parents=True, exist_ok=True)
    with FREQ_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mnemonic", "count", "sail_supported"])
        for mn, cnt, sup in rows:
            w.writerow([mn, cnt, sup])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="Only process first N kernels")
    ap.add_argument("--bare-metal", action="store_true",
                    help="Also run on GPU and diff dumps")
    args = ap.parse_args()

    hips = sorted(GEN_DIR.glob("*.hip"))
    if args.limit:
        hips = hips[: args.limit]

    if not hips:
        print(f"No kernels in {GEN_DIR}. Run generate_kernels.py first.",
              file=sys.stderr)
        sys.exit(1)

    emu = _ensure_emu()
    exp._diff.SETUP_DIR.mkdir(parents=True, exist_ok=True)
    exp.EXP_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    ASM_OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Clear stale .s from prior runs so the frequency table reflects this corpus.
    for stale in ASM_OUT_DIR.glob("*.s"):
        stale.unlink()

    meta_by_name = _load_manifest_meta()
    supported = _load_sail_supported_mnemonics()

    fields = ["kernel", "compile", "sail", "hazards", "unsupported",
              "unsupported_inst", "hip", "dump", "notes"]
    rows = []
    for i, p in enumerate(hips, 1):
        print(f"[{i}/{len(hips)}] {p.stem}", flush=True)
        try:
            rows.append(run_one(p, args.bare_metal, emu,
                                meta_by_name, supported))
        except Exception as e:
            rows.append({"kernel": p.stem, "compile": "error",
                         "sail": "", "hazards": "", "unsupported": "",
                         "unsupported_inst": "",
                         "hip": "n/a", "dump": "n/a",
                         "notes": f"unexpected: {e}"[:300]})

    with RESULTS_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    freq = _aggregate_frequencies(supported)

    n_total = len(rows)
    n_compiled = sum(1 for r in rows if r["compile"] == "ok")
    n_sail_ok = sum(1 for r in rows if r["sail"] == "ok")
    n_unsupported = sum(1 for r in rows if r["sail"] == "unsupported")
    n_hazard = sum(1 for r in rows if r["hazards"])
    interesting = [r for r in rows
                   if r["hazards"] and r["compile"] == "ok"
                   and r["sail"] in ("ok", "unsupported")]

    print()
    print(f"Total kernels        : {n_total}")
    print(f"Compiled             : {n_compiled}")
    print(f"Sail executed ok     : {n_sail_ok}")
    print(f"Sail unsupported     : {n_unsupported}")
    print(f"Oracle hazards flagged: {n_hazard}")
    print(f"Hazard on clean output: {len(interesting)}  <-- INTERESTING")
    if interesting:
        print("\nClean-compilation hazards:")
        for r in interesting:
            print(f"  {r['kernel']}: {r['hazards']}")

    unsupported_only = [(mn, cnt) for mn, cnt, sup in freq if sup == "n"]
    print(f"\nFrequency CSV: {FREQ_CSV}")
    print("Top 10 unsupported instructions:")
    for mn, cnt in unsupported_only[:10]:
        print(f"  {cnt:5d}  {mn}")

    print(f"\nResults CSV: {RESULTS_CSV}")


if __name__ == "__main__":
    main()

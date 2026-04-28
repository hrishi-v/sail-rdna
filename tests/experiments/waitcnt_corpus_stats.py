#!/usr/bin/env python3
"""
Characterise s_waitcnt usage across an LLVM-generated AMDGPU assembly corpus.

Walks every .s file under the given roots (default: build/experimental/),
parses every s_waitcnt and s_waitcnt_vscnt instruction, and reports:

  * Total occurrences per counter type (vmcnt, lgkmcnt, expcnt, vscnt).
  * Histogram of immediate values (so N=0 vs N>0 is visible).
  * Full-drain (N=0) vs partial-drain (N>0) split per counter.
  * Per-kernel breakdown to surface outliers (e.g. a kernel with a
    partial LGKMCNT or VSCNT drain).

Counter handling notes:
  * GFX10+ split: vscnt is its own instruction (s_waitcnt_vscnt), not
    a field of s_waitcnt. Both forms are parsed.
  * Disassembly uses named counters in this corpus, but the script also
    decodes a raw immediate form (e.g. "s_waitcnt 0xc07f") using the
    GFX10 encoding: VMCNT={[15:14],[3:0]}, EXPCNT=[6:4], LGKMCNT=[13:8].
  * Kernel attribution uses the most recent ".type NAME,@function"
    directive. Lines outside any function are attributed to "<file>".

Outputs:
  * Console summary table.
  * CSV with one row per (file, kernel, counter, value): long-form so
    histograms and per-kernel breakdowns can be regenerated downstream.
  * CSV with the aggregate per-counter summary.

Usage:
    python tests/experiments/waitcnt_corpus_stats.py
    python tests/experiments/waitcnt_corpus_stats.py build/experimental tests/asm
    python tests/experiments/waitcnt_corpus_stats.py --out-dir tests/experiments/results
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# GFX10 s_waitcnt encoding field widths.
VMCNT_MAX = 0x3F   # 6-bit, split [15:14]:[3:0]
EXPCNT_MAX = 0x7   # 3-bit, [6:4]
LGKMCNT_MAX = 0x3F # 6-bit, [13:8]

COUNTERS = ("vmcnt", "lgkmcnt", "expcnt", "vscnt")

# Match named-form fields anywhere in an s_waitcnt operand list.
NAMED_FIELD_RE = re.compile(r"\b(vmcnt|lgkmcnt|expcnt)\s*\(\s*(\d+)\s*\)")
# Bare-immediate s_waitcnt form: "s_waitcnt 0xc07f" or "s_waitcnt 49279".
IMM_RE = re.compile(r"^\s*(0x[0-9a-fA-F]+|\d+)\s*$")
# Recognise the two opcode forms.
WAITCNT_RE = re.compile(r"^\s*s_waitcnt\b(?!_)\s*(.*?)\s*(?://.*)?$")
WAITCNT_VSCNT_RE = re.compile(r"^\s*s_waitcnt_vscnt\b\s*(.*?)\s*(?://.*)?$")
# .type NAME,@function — function-kind .type directives only.
TYPE_FUNC_RE = re.compile(r"^\s*\.type\s+([A-Za-z_][\w$.]*)\s*,\s*@function\b")


@dataclass(frozen=True)
class Event:
    file: str
    kernel: str
    line: int
    counter: str
    value: int
    raw: str


def decode_imm(imm: int) -> dict[str, int]:
    """Decode a raw GFX10 s_waitcnt 16-bit immediate into named counters."""
    vmcnt = ((imm >> 14) & 0x3) << 4 | (imm & 0xF)
    expcnt = (imm >> 4) & 0x7
    lgkmcnt = (imm >> 8) & 0x3F
    return {"vmcnt": vmcnt, "lgkmcnt": lgkmcnt, "expcnt": expcnt}


def parse_vscnt_operand(operand: str) -> int | None:
    """s_waitcnt_vscnt [null,] N   -> N (decimal or hex). None if unparsable."""
    parts = [p.strip() for p in operand.split(",")]
    tail = parts[-1] if parts else ""
    m = IMM_RE.match(tail)
    if not m:
        return None
    tok = m.group(1)
    return int(tok, 16) if tok.lower().startswith("0x") else int(tok)


def is_default_unmasked(values: dict[str, int]) -> bool:
    """A bare s_waitcnt with the default mask is a no-op; treat carefully."""
    return (
        values.get("vmcnt") == VMCNT_MAX
        and values.get("lgkmcnt") == LGKMCNT_MAX
        and values.get("expcnt") == EXPCNT_MAX
    )


def parse_file(path: Path) -> list[Event]:
    events: list[Event] = []
    current_kernel = f"<{path.name}>"
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        print(f"warn: cannot read {path}: {exc}", file=sys.stderr)
        return events

    for lineno, raw_line in enumerate(text.splitlines(), 1):
        # Strip line comments early but keep operand text intact.
        line = raw_line.split(";", 1)[0]

        m_type = TYPE_FUNC_RE.match(line)
        if m_type:
            current_kernel = m_type.group(1)
            continue

        m_vsc = WAITCNT_VSCNT_RE.match(line)
        if m_vsc:
            v = parse_vscnt_operand(m_vsc.group(1))
            if v is not None:
                events.append(
                    Event(str(path), current_kernel, lineno, "vscnt", v, raw_line.strip())
                )
            continue

        m_w = WAITCNT_RE.match(line)
        if m_w:
            operand = m_w.group(1)
            named = NAMED_FIELD_RE.findall(operand)
            if named:
                for name, val in named:
                    events.append(
                        Event(
                            str(path),
                            current_kernel,
                            lineno,
                            name,
                            int(val),
                            raw_line.strip(),
                        )
                    )
                continue
            # Fallback: raw immediate form.
            m_imm = IMM_RE.match(operand)
            if m_imm:
                tok = m_imm.group(1)
                imm = int(tok, 16) if tok.lower().startswith("0x") else int(tok)
                decoded = decode_imm(imm)
                if is_default_unmasked(decoded):
                    # Encoded no-op; skip — would skew "partial drain" counts.
                    continue
                for name, val in decoded.items():
                    events.append(
                        Event(
                            str(path),
                            current_kernel,
                            lineno,
                            name,
                            val,
                            raw_line.strip(),
                        )
                    )
    return events


def find_corpus(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".s":
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.s")))
        else:
            print(f"warn: {root} is not a file or directory", file=sys.stderr)
    return files


def histogram(values: list[int]) -> Counter:
    return Counter(values)


def print_summary(events: list[Event], n_files: int, kernels: set[str]) -> None:
    by_counter: dict[str, list[int]] = defaultdict(list)
    for e in events:
        by_counter[e.counter].append(e.value)

    print(f"\nCorpus: {n_files} files, {len(kernels)} kernels, "
          f"{len(events)} counter-events parsed from s_waitcnt[_vscnt].\n")

    header = f"{'counter':<8} {'total':>7} {'full(N=0)':>10} {'partial(N>0)':>13} {'max':>5} {'distinct':>9}"
    print(header)
    print("-" * len(header))
    for c in COUNTERS:
        vals = by_counter.get(c, [])
        if not vals:
            print(f"{c:<8} {0:>7} {0:>10} {0:>13} {'-':>5} {0:>9}")
            continue
        total = len(vals)
        full = sum(1 for v in vals if v == 0)
        partial = total - full
        print(f"{c:<8} {total:>7} {full:>10} {partial:>13} "
              f"{max(vals):>5} {len(set(vals)):>9}")

    print("\nValue histograms (value: count):")
    for c in COUNTERS:
        vals = by_counter.get(c, [])
        if not vals:
            print(f"  {c}: <none>")
            continue
        hist = histogram(vals)
        # Show 0 first (full drains), then sorted descending by frequency.
        ordered = []
        if 0 in hist:
            ordered.append((0, hist[0]))
        ordered.extend(sorted(((v, n) for v, n in hist.items() if v != 0),
                              key=lambda x: (-x[1], x[0])))
        rendered = ", ".join(f"{v}:{n}" for v, n in ordered)
        print(f"  {c}: {rendered}")


def per_kernel_outliers(events: list[Event]) -> list[tuple[str, str, int, int]]:
    """Return kernels with at least one partial drain, per counter type.

    Tuple: (kernel, counter, partial_count, total_count_for_counter).
    """
    by_kc: dict[tuple[str, str], list[int]] = defaultdict(list)
    for e in events:
        by_kc[(e.kernel, e.counter)].append(e.value)
    rows = []
    for (kernel, counter), vals in by_kc.items():
        partial = sum(1 for v in vals if v > 0)
        if partial:
            rows.append((kernel, counter, partial, len(vals)))
    rows.sort(key=lambda r: (r[1], -r[2], r[0]))
    return rows


def write_events_csv(events: list[Event], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "kernel", "line", "counter", "value", "raw"])
        for e in events:
            w.writerow([e.file, e.kernel, e.line, e.counter, e.value, e.raw])


def write_summary_csv(events: list[Event], path: Path) -> None:
    by_counter: dict[str, list[int]] = defaultdict(list)
    for e in events:
        by_counter[e.counter].append(e.value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["counter", "value", "count"])
        for c in COUNTERS:
            hist = histogram(by_counter.get(c, []))
            for v in sorted(hist):
                w.writerow([c, v, hist[v]])


def write_per_kernel_csv(events: list[Event], path: Path) -> None:
    by_kc: dict[tuple[str, str], list[int]] = defaultdict(list)
    for e in events:
        by_kc[(e.kernel, e.counter)].append(e.value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kernel", "counter", "total", "full_drains",
                    "partial_drains", "max_value"])
        for (kernel, counter), vals in sorted(by_kc.items()):
            full = sum(1 for v in vals if v == 0)
            partial = len(vals) - full
            w.writerow([kernel, counter, len(vals), full, partial, max(vals)])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument(
        "roots",
        nargs="*",
        type=Path,
        default=[Path("build/experimental")],
        help="Files or directories to scan (default: build/experimental).",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("tests/experiments/results"),
        help="Directory for CSV outputs.",
    )
    ap.add_argument(
        "--prefix",
        default="waitcnt_corpus",
        help="CSV filename prefix (default: waitcnt_corpus).",
    )
    ap.add_argument(
        "--show-outliers",
        type=int,
        default=20,
        help="Max kernels to print with partial drains per counter (default 20).",
    )
    args = ap.parse_args(argv)

    files = find_corpus(args.roots)
    if not files:
        print("error: no .s files found under given roots", file=sys.stderr)
        return 1

    all_events: list[Event] = []
    kernels: set[str] = set()
    for f in files:
        evs = parse_file(f)
        for e in evs:
            kernels.add(e.kernel)
        all_events.extend(evs)

    print_summary(all_events, len(files), kernels)

    outliers = per_kernel_outliers(all_events)
    print(f"\nKernels with partial drains "
          f"(value>0) — {len(outliers)} (kernel, counter, partial, total):")
    if outliers:
        # Group printout by counter for readability.
        by_counter = defaultdict(list)
        for kernel, counter, partial, total in outliers:
            by_counter[counter].append((kernel, partial, total))
        for c in COUNTERS:
            rows = by_counter.get(c, [])
            if not rows:
                print(f"  {c}: none")
                continue
            print(f"  {c}: {len(rows)} kernel(s)")
            shown = sorted(rows, key=lambda r: (-r[1], r[0]))[: args.show_outliers]
            for kernel, partial, total in shown:
                print(f"    {kernel:<60} {partial:>5}/{total}")
            if len(rows) > args.show_outliers:
                print(f"    ... +{len(rows) - args.show_outliers} more")
    else:
        print("  (none)")

    events_csv = args.out_dir / f"{args.prefix}_events.csv"
    summary_csv = args.out_dir / f"{args.prefix}_summary.csv"
    per_kernel_csv = args.out_dir / f"{args.prefix}_per_kernel.csv"
    write_events_csv(all_events, events_csv)
    write_summary_csv(all_events, summary_csv)
    write_per_kernel_csv(all_events, per_kernel_csv)

    print(f"\nWrote:\n  {events_csv}\n  {summary_csv}\n  {per_kernel_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

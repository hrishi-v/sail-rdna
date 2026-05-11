#!/usr/bin/env python3
"""Inventory VOP2-with-32-bit-literal occurrences in the evaluation corpus."""
from __future__ import annotations
import csv
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/hrishi/Documents/sail-rdna")
BUILD = ROOT / "tests/mutation/build"
RESULTS_DIR = ROOT / "results"
MUT_DIR = ROOT / "tests/mutation"


def extract_text(elf: Path) -> bytes:
    r = subprocess.run(
        ["llvm-objcopy", "--dump-section", f".text=/dev/stdout", str(elf), "/dev/null"],
        capture_output=True,
    )
    if r.returncode != 0:
        return b""
    return r.stdout


def src_is_literal(field9: int) -> bool:
    return field9 == 0xFF


def scan(text: bytes):
    """Return (count_vop2_literal, total_vop2, positions[0..1], stream_words).
    positions = list of fractional positions (instr_index / total_instr_count)."""
    n = len(text) // 4
    if n == 0:
        return 0, 0, [], 0, 0
    words = struct.unpack_from(f"<{n}I", text, 0)

    i = 0
    total_vop2 = 0
    vop2_lit = 0
    positions = []
    instr_index = 0
    instr_total_pass1 = 0

    # First pass: walk to count total instructions properly, also record vop2-lit
    # positions in instruction-index space. Then convert to fractional.
    while i < n:
        w = words[i]
        # Stop at s_endpgm (BFB00000) — everything after is s_code_end padding.
        if w == 0xBFB00000:
            instr_index += 1
            i += 1
            break
        bit31 = (w >> 31) & 1
        b30_25 = (w >> 25) & 0x3F
        b31_26 = (w >> 26) & 0x3F
        b31_30 = (w >> 30) & 0x3
        b29_23 = (w >> 23) & 0x7F
        b29_28 = (w >> 28) & 0x3
        consumes_w1 = False
        instr_len = 4
        is_vop2 = False
        src0 = w & 0x1FF
        ssrc0 = w & 0xFF
        ssrc1 = (w >> 8) & 0xFF

        if bit31 == 0:
            # VOP1 / VOPC / VOP2 family (single dword, may have 32-bit literal)
            if b30_25 == 0b111111:
                # VOP1
                if src_is_literal(src0):
                    instr_len = 8
            elif b30_25 == 0b111110:
                # VOPC
                if src_is_literal(src0):
                    instr_len = 8
            else:
                # VOP2
                is_vop2 = True
                if src_is_literal(src0):
                    instr_len = 8
                    vop2_lit += 1
                    positions.append(instr_index)  # placeholder, fix later
        else:
            if b31_26 == 0b110101:
                # VOP3 (dword pair, 64-bit)
                instr_len = 8
            elif b31_26 == 0b111101:
                # SMEM (dword pair)
                instr_len = 8
            elif b31_26 == 0b110111:
                # FLAT (dword pair)
                instr_len = 8
            elif b31_26 == 0b110110:
                # DS (dword pair)
                instr_len = 8
            elif b31_26 == 0b111000:
                # MUBUF (dword pair)
                instr_len = 8
            elif b31_30 == 0b10:
                # SOP* family — single dword, may carry 32-bit literal in ssrc0/ssrc1
                if b29_23 == 0b1111101:
                    # SOP1: ssrc0 in [7:0]
                    if ssrc0 == 0xFF:
                        instr_len = 8
                elif b29_23 == 0b1111110:
                    # SOPC: ssrc0/ssrc1
                    if ssrc0 == 0xFF or ssrc1 == 0xFF:
                        instr_len = 8
                elif b29_23 == 0b1111111:
                    # SOPP: no literal
                    pass
                elif b29_28 == 0b11:
                    # SOPK: 16-bit imm inside instr — no extra literal
                    pass
                else:
                    # SOP2: ssrc0 / ssrc1
                    if ssrc0 == 0xFF or ssrc1 == 0xFF:
                        instr_len = 8
            else:
                # Unknown — advance 4
                pass

        if is_vop2:
            total_vop2 += 1
        i += instr_len // 4
        instr_index += 1

    instr_total_pass1 = instr_index
    # Convert positions (instruction indices) to fractional 0..1
    frac_positions = [p / instr_total_pass1 if instr_total_pass1 > 0 else 0.0 for p in positions]
    return vop2_lit, total_vop2, frac_positions, instr_total_pass1, n


def main():
    elfs = sorted(BUILD.glob("_mutant_*.elf"))
    print(f"Total _mutant_*.elf: {len(elfs)}", file=sys.stderr)

    # Also scan _orig*.elf (kernel originals)
    origs = sorted(BUILD.glob("_orig*.elf"))
    print(f"Total _orig*.elf: {len(origs)}", file=sys.stderr)

    inv = {}  # filename -> dict(count, total_vop2, frac_positions, total_instrs)
    for elf in elfs + origs:
        text = extract_text(elf)
        c, tv, fp, total_instrs, nwords = scan(text)
        inv[elf.name] = {
            "vop2_lit": c,
            "vop2_total": tv,
            "positions": fp,
            "total_instrs": total_instrs,
            "words": nwords,
        }

    out = ROOT / "results/vop2_literal_inventory.json"
    with open(out, "w") as f:
        json.dump(inv, f)
    print(f"Wrote {out}", file=sys.stderr)

    # Summary
    mutants = [inv[e.name] for e in elfs]
    nzero = sum(1 for m in mutants if m["vop2_lit"] == 0)
    nany = sum(1 for m in mutants if m["vop2_lit"] >= 1)
    counts = [m["vop2_lit"] for m in mutants if m["vop2_lit"] >= 1]
    mean = sum(counts) / len(counts) if counts else 0.0
    mx = max(counts) if counts else 0
    print(f"--- Mutant ELF summary ({len(mutants)}) ---")
    print(f"Zero VOP2-literal: {nzero}")
    print(f">=1 VOP2-literal:  {nany}  (mean={mean:.2f}, max={mx})")

    # Top 10 by count
    ranked = sorted(((e.name, inv[e.name]["vop2_lit"]) for e in elfs), key=lambda x: -x[1])[:10]
    print("Top 10:")
    for name, c in ranked:
        print(f"  {c:4d}  {name}")

    # Position bucketing
    all_positions = []
    for m in mutants:
        all_positions.extend(m["positions"])
    n_first = sum(1 for p in all_positions if p < 0.2)
    n_last = sum(1 for p in all_positions if p >= 0.8)
    n_mid = len(all_positions) - n_first - n_last
    print(f"Position buckets ({len(all_positions)} total occurrences):")
    if all_positions:
        print(f"  first 20%: {n_first} ({100*n_first/len(all_positions):.1f}%)")
        print(f"  middle:    {n_mid} ({100*n_mid/len(all_positions):.1f}%)")
        print(f"  last 20%:  {n_last} ({100*n_last/len(all_positions):.1f}%)")


if __name__ == "__main__":
    main()

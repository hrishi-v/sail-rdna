from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

# Maps register name -> per-lane values.
# Scalar registers have a single-element list; vector registers have WAVE_SIZE elements.
RegisterDump: TypeAlias = dict[str, list[int]]


def parse_register_file(path: Path) -> RegisterDump:
    """Parse a register dump file into a RegisterDump.
    """
    result: RegisterDump = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        reg, _, values_str = line.partition(":")
        result[reg.strip()] = [int(v, 16) for v in values_str.split()]
    return result


def sail_scalar_dumps(dump_dir: Path) -> dict[str, RegisterDump]:
    """Parse all Sail scalar register dumps from outputs/register_dumps/scal_*.log."""
    return {
        path.stem.removeprefix("scal_"): parse_register_file(path)
        for path in dump_dir.glob("scal_*.log")
    }


def sail_vector_dumps(dump_dir: Path) -> dict[str, RegisterDump]:
    """Parse all Sail vector register dumps from outputs/register_dumps/vec_*.log."""
    return {
        path.stem.removeprefix("vec_"): parse_register_file(path)
        for path in dump_dir.glob("vec_*.log")
    }


def hip_vector_dumps(output_dir: Path) -> dict[str, RegisterDump]:
    """Parse all HIP vector register dumps from bare_metal_test/outputs/*_vector_registers."""
    return {
        path.name.removesuffix("_vector_registers"): parse_register_file(path)
        for path in output_dir.iterdir()
        if path.name.endswith("_vector_registers")
    }

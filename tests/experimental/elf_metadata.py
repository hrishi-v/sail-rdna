from __future__ import annotations

from pathlib import Path

import msgpack
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import NoteSection

NT_AMDGPU_METADATA = 0x20

KERNARG_BASE = 0x1000
DATA_BUFFER_BASE = 0x2000
DATA_BUFFER_STRIDE = 0x200
WORDS_PER_BUFFER = 32

_SUPPORTED_VALUE_KINDS = frozenset({"global_buffer", "by_value"})


def pattern_for(buffer_index: int, word_index: int) -> int:
    return (0xDEAD0000 + (buffer_index << 5) + word_index) & 0xFFFFFFFF


def _find_amdgpu_metadata_blob(elf_path: Path) -> bytes:
    with open(elf_path, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if not isinstance(section, NoteSection):
                continue
            for note in section.iter_notes():
                if note["n_name"] == "AMDGPU" and note["n_type"] == NT_AMDGPU_METADATA:
                    return note["n_desc"]
    raise RuntimeError(
        f"ELF {elf_path} has no AMDGPU metadata note "
        f"(name='AMDGPU', type=0x{NT_AMDGPU_METADATA:x})"
    )


def parse_kernel_args(elf_path: Path, kernel_name: str) -> list[dict]:
    """Extract `.args` for `kernel_name` from an AMDGPU code-object v4 ELF.

    Returns a list of dicts with keys `value_kind`, `offset`, `size`, in the
    original order. Raises `RuntimeError` for any shape we don't handle.
    """
    blob = _find_amdgpu_metadata_blob(elf_path)
    try:
        meta = msgpack.unpackb(blob, raw=False)
    except Exception as e:
        raise RuntimeError(f"AMDGPU metadata msgpack decode failed: {e}") from e

    kernels = meta.get("amdhsa.kernels")
    if not kernels:
        raise RuntimeError("AMDGPU metadata has no 'amdhsa.kernels' entries")

    kernel = next((k for k in kernels if k.get(".name") == kernel_name), None)
    if kernel is None:
        names = [k.get(".name") for k in kernels]
        raise RuntimeError(
            f"Kernel '{kernel_name}' not found in metadata (have: {names})"
        )

    raw_args = kernel.get(".args")
    if raw_args is None:
        raise RuntimeError(f"Kernel '{kernel_name}' has no '.args' in metadata")

    parsed: list[dict] = []
    for i, a in enumerate(raw_args):
        vk = a.get(".value_kind")
        if vk not in _SUPPORTED_VALUE_KINDS:
            raise RuntimeError(
                f"Kernel '{kernel_name}' arg {i} has unsupported value_kind "
                f"'{vk}' (supported: {sorted(_SUPPORTED_VALUE_KINDS)})"
            )
        parsed.append({
            "value_kind": vk,
            "offset": int(a[".offset"]),
            "size": int(a[".size"]),
        })
    return parsed

from __future__ import annotations

import itertools
import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "generated"

HEADER = '#include <hip/hip_runtime.h>\n\n'

_OP_TAG = {"+": "add", "-": "sub", "&": "and", "|": "or", "^": "xor", "*": "mul"}

ACCUM_OPS = ["+", "-", "&", "|", "^"]
ACCUM_NS = [4, 8, 16, 32, 64, 96]

LOOP_ACCUM_OPS = ["+", "^"]
LOOP_ACCUM_NS = [8, 16, 32, 64, 128]

STORE_CHAIN_NS = [4, 8, 16, 32, 64]
LOAD_COMPUTE_STORE_NS = [4, 8, 16]

RMW_OPS = ["+", "-", "&", "|", "^", "*"]
RMW_CONSTS = [1, 7, 42, 0xDEAD]

RMW_IDX_OPS = ["+", "^"]
RMW_IDX_CONSTS = [1, 42]
RMW_IDX_INDICES = [0, 1, 8]

TWO_BUF_OPS = ["+", "-", "*", "&", "|", "^"]

MIXED_OPS = ["+", "^"]
MIXED_CONSTS = [1, 42]

STORELOAD_C1 = [1, 42, 0xDEAD]
STORELOAD_C2 = [1, 7]

REGS_PRESSURE_NS = [32, 64, 128]
DEEP_CHAIN_NS = [16, 32, 64]
MIXED_LOADS_NS = [8, 16, 32]

TID = "int tid = blockIdx.x * blockDim.x + threadIdx.x;"
BEGIN = '__asm__ volatile("; BEGIN");'
END = '__asm__ volatile("; END");'


def _pin_v5(expr: str) -> str:
    return f'__asm__ volatile("v_mov_b32 v5, %0" : : "v"({expr}));'


def _wrap(src: str) -> str:
    return HEADER + src


def _init_for(op: str) -> str:
    if op == "&":
        return "-1"
    if op == "*":
        return "1"
    return "0"


def _hex_tag(c: int) -> str:
    if c >= 16:
        return f"0x{c:X}"
    return str(c)


def _c_literal(c: int) -> str:
    return f"0x{c:X}" if c >= 16 else str(c)


def gen_accum(op: str, n: int):
    tag = _OP_TAG[op]
    name = f"accum_{tag}_{n}"
    params = ["int* out"] + [f"int* b{i}" for i in range(n)]
    init = _init_for(op)
    loads = " ".join(f"s {op}= b{i}[tid];" for i in range(n))
    src = (
        f'extern "C" __global__ void {name}({", ".join(params)}) {{\n'
        f"    {TID}\n"
        f"    int s = {init};\n"
        f"    {BEGIN}\n"
        f"    {loads}\n"
        f"    {_pin_v5('s')}\n"
        f"    {END}\n"
        f"    out[tid] = s;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "accum_n_distinct", "op": op, "N": n}


def gen_loop_accum(op: str, n: int):
    tag = _OP_TAG[op]
    name = f"loop_accum_{tag}_{n}"
    init = _init_for(op)
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    int s = {init};\n"
        f"    {BEGIN}\n"
        f"    #pragma unroll\n"
        f"    for (int i = 0; i < {n}; i++) s {op}= buf[i * 32 + tid];\n"
        f"    {_pin_v5('s')}\n"
        f"    {END}\n"
        f"    out[tid] = s;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "loop_accum", "op": op, "N": n, "opt": "-O2"}


def gen_store_chain(n: int):
    name = f"store_chain_{n}"
    params = ["int* out"] + [f"int* b{i}" for i in range(n)]
    stores = " ".join(f"b{i}[tid] = tid * {i + 1};" for i in range(n))
    src = (
        f'extern "C" __global__ void {name}({", ".join(params)}) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    {stores}\n"
        f"    int r = tid;\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"    out[tid] = r;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "store_chain", "N": n}


def gen_load_overwrite():
    name = "load_overwrite"
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int a = buf[tid];\n"
        f"    a = 42;\n"
        f"    {_pin_v5('a')}\n"
        f"    {END}\n"
        f"    out[tid] = a;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "load_overwrite"}


def gen_store_then_load():
    name = "store_then_load"
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    buf[tid] = tid + 42;\n"
        f"    int v = buf[tid];\n"
        f"    {_pin_v5('v')}\n"
        f"    {END}\n"
        f"    out[tid] = v;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "store_then_load"}


def gen_fanout():
    name = "fanout"
    src = (
        f'extern "C" __global__ void {name}(int* out, int* o1, int* o2, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int v = buf[tid];\n"
        f"    out[tid] = v + 1;\n"
        f"    o1[tid]  = v * 2;\n"
        f"    o2[tid]  = v ^ 0xDEAD;\n"
        f"    {_pin_v5('v')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "fanout"}


def gen_load_compute_store(n: int):
    name = f"load_compute_store_{n}"
    params = ["int* out"] + [f"int* b{i}" for i in range(n)]
    body_lines = []
    for i in range(n):
        body_lines.append(f"int v{i} = b{i}[tid];")
        body_lines.append(f"int r{i} = v{i} ^ {i + 1};")
        body_lines.append(f"b{i}[tid] = r{i};")
    body = "\n    ".join(body_lines)
    final = " ^ ".join(f"r{i}" for i in range(n))
    src = (
        f'extern "C" __global__ void {name}({", ".join(params)}) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    {body}\n"
        f"    int r = {final};\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"    out[tid] = r;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "load_compute_store", "N": n}


def gen_rmw(op: str, const: int):
    tag = _OP_TAG[op]
    name = f"rmw_{tag}_c{_hex_tag(const)}"
    src = (
        f'extern "C" __global__ void {name}(int* out) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int v = out[tid];\n"
        f"    v = v {op} {_c_literal(const)};\n"
        f"    out[tid] = v;\n"
        f"    {_pin_v5('v')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "rmw", "op": op, "const": const}


def gen_rmw_idx(op: str, const: int, idx: int):
    tag = _OP_TAG[op]
    name = f"rmw_idx_{tag}_c{_hex_tag(const)}_i{idx}"
    src = (
        f'extern "C" __global__ void {name}(int* out) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int v = out[{idx}];\n"
        f"    v = v {op} {_c_literal(const)};\n"
        f"    out[{idx}] = v;\n"
        f"    {_pin_v5('v')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "rmw_idx", "op": op, "const": const, "idx": idx}


def gen_two_buf(op: str):
    tag = _OP_TAG[op]
    name = f"two_buf_{tag}"
    src = (
        f'extern "C" __global__ void {name}(int* out, int* a, int* b) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int r = a[tid] {op} b[tid];\n"
        f"    out[tid] = r;\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "two_buf", "op": op}


def gen_mixed(op1: str, c1: int, op2: str, c2: int):
    t1, t2 = _OP_TAG[op1], _OP_TAG[op2]
    name = f"mixed_{t1}_c{_hex_tag(c1)}_{t2}_c{_hex_tag(c2)}"
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int r = (buf[tid] {op1} {_c_literal(c1)}) {op2} {_c_literal(c2)};\n"
        f"    out[tid] = r;\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "mixed_const",
                              "op1": op1, "c1": c1, "op2": op2, "c2": c2}


def gen_storeload(c1: int, c2: int):
    name = f"storeload_c{_hex_tag(c1)}_c{_hex_tag(c2)}"
    src = (
        f'extern "C" __global__ void {name}(int* out) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    out[tid] = {_c_literal(c1)};\n"
        f"    int x = out[tid] + {_c_literal(c2)};\n"
        f"    out[tid] = x;\n"
        f"    {_pin_v5('x')}\n"
        f"    {END}\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "store_reload", "c1": c1, "c2": c2}


def gen_regs_pressure(n: int):
    name = f"regs_pressure_{n}"
    loads = "\n    ".join(f"int v{i} = buf[{i} * 32 + tid];" for i in range(n))
    combine = "\n    ".join(
        f"int r{i} = v{i} ^ (v{(i + 1) % n} + {i + 1});" for i in range(n)
    )
    final = " ^ ".join(f"r{i}" for i in range(n))
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    {loads}\n"
        f"    {combine}\n"
        f"    int r = {final};\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"    out[tid] = r;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "regs_pressure", "N": n}


def gen_deep_chain(n: int):
    name = f"deep_chain_{n}"
    steps = "\n    ".join(
        f"v = buf[v & 31];" for _ in range(n)
    )
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    {TID}\n"
        f"    {BEGIN}\n"
        f"    int v = buf[tid & 31];\n"
        f"    {steps}\n"
        f"    {_pin_v5('v')}\n"
        f"    {END}\n"
        f"    out[tid] = v;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "deep_chain", "N": n}


def gen_mixed_loads(n: int):
    name = f"mixed_loads_{n}"
    pairs = []
    for i in range(n):
        pairs.append(f"r += buf[{i} * 32 + tid];")
        pairs.append(f"r ^= lds[(tid + {i}) & 31];")
    body = "\n    ".join(pairs)
    src = (
        f'extern "C" __global__ void {name}(int* out, int* buf) {{\n'
        f"    __shared__ int lds[32];\n"
        f"    {TID}\n"
        f"    lds[threadIdx.x & 31] = threadIdx.x * 3 + 7;\n"
        f"    __syncthreads();\n"
        f"    {BEGIN}\n"
        f"    int r = 0;\n"
        f"    {body}\n"
        f"    {_pin_v5('r')}\n"
        f"    {END}\n"
        f"    out[tid] = r;\n"
        f"}}\n"
    )
    return name, _wrap(src), {"template": "mixed_loads", "N": n}


def generate_all():
    kernels = []

    for op, n in itertools.product(ACCUM_OPS, ACCUM_NS):
        kernels.append(gen_accum(op, n))
    for op, n in itertools.product(LOOP_ACCUM_OPS, LOOP_ACCUM_NS):
        kernels.append(gen_loop_accum(op, n))
    for n in STORE_CHAIN_NS:
        kernels.append(gen_store_chain(n))

    kernels.append(gen_load_overwrite())
    kernels.append(gen_store_then_load())
    kernels.append(gen_fanout())
    for n in LOAD_COMPUTE_STORE_NS:
        kernels.append(gen_load_compute_store(n))

    for op, c in itertools.product(RMW_OPS, RMW_CONSTS):
        kernels.append(gen_rmw(op, c))
    for op, c, i in itertools.product(RMW_IDX_OPS, RMW_IDX_CONSTS, RMW_IDX_INDICES):
        kernels.append(gen_rmw_idx(op, c, i))
    for op in TWO_BUF_OPS:
        kernels.append(gen_two_buf(op))
    for op1, c1, op2, c2 in itertools.product(MIXED_OPS, MIXED_CONSTS,
                                              MIXED_OPS, MIXED_CONSTS):
        kernels.append(gen_mixed(op1, c1, op2, c2))
    for c1, c2 in itertools.product(STORELOAD_C1, STORELOAD_C2):
        kernels.append(gen_storeload(c1, c2))

    for n in REGS_PRESSURE_NS:
        kernels.append(gen_regs_pressure(n))
    for n in DEEP_CHAIN_NS:
        kernels.append(gen_deep_chain(n))
    for n in MIXED_LOADS_NS:
        kernels.append(gen_mixed_loads(n))

    return kernels


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob("*.hip"):
        p.unlink()
    seen = set()
    entries = []
    for name, src, meta in generate_all():
        if name in seen:
            continue
        seen.add(name)
        (OUT_DIR / f"{name}.hip").write_text(src)
        entries.append({"name": name, **meta})
    (OUT_DIR / "manifest.json").write_text(json.dumps(entries, indent=2))
    print(f"Generated {len(entries)} kernels in {OUT_DIR}")


if __name__ == "__main__":
    main()

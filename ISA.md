# RDNA3 Sail — Supported ISA

Instructions currently implemented in the Sail specification (`spec/`).

---

## SOP2 — Scalar ALU (Two Source)

| Instruction | Description | Flags |
|---|---|---|
| `S_ADD_U32 sdst, ssrc0, ssrc1` | `sdst = ssrc0 + ssrc1` | SCC = carry out |
| `S_SUB_U32 sdst, ssrc0, ssrc1` | `sdst = ssrc0 - ssrc1` | SCC = borrow out |
| `S_LSHR_B64 sdst, ssrc0, ssrc1` | `sdst[63:0] = ssrc0[63:0] >> ssrc1[5:0]` (logical) | SCC = result != 0 |
| `S_CSELECT_B32 sdst, ssrc0, ssrc1` | `sdst = SCC ? ssrc0 : ssrc1` | — |

---

## SOP1 — Scalar ALU (One Source)

| Instruction | Description | Flags |
|---|---|---|
| `S_MOV_B32 sdst, ssrc` | `sdst = ssrc` | — |
| `S_MOV_B64 sdst, ssrc` | `sdst[63:0] = ssrc[63:0]` | — |

---

## SOPC — Scalar Compare

| Instruction | Description | Flags |
|---|---|---|
| `S_CMP_EQ_I32 ssrc0, ssrc1` | SCC = (ssrc0 == ssrc1) | SCC |
| `S_CMP_LG_I32 ssrc0, ssrc1` | SCC = (ssrc0 != ssrc1) | SCC |

---

## SOPP — Scalar Program Flow

| Instruction | Description |
|---|---|
| `S_WAITCNT lgkmcnt(n)` | Wait for scalar/LDS memory ops (no-op in sim) |
| `S_ENDPGM` | Halt execution, set halt flag |

---

## VOP2 / VOP3 — Vector ALU

All vector instructions operate per-lane, gated by the EXEC mask.

| Instruction | Description | Flags |
|---|---|---|
| `V_MOV_B32 vdst, src` | `vdst[lane] = src` for each active lane | — |
| `V_ADD_NC_U32 vdst, src0, src1` | `vdst[lane] = src0[lane] + src1[lane]` (no carry out) | — |

`src` can be a VGPR, SGPR, or inline immediate. SGPR sources are broadcast across all active lanes.

---

## SMEM — Scalar Memory

| Instruction | Description |
|---|---|
| `S_LOAD_B64 sdst, sbase, offset` | Load 64 bits from `sbase[63:0] + offset` into SGPR pair `sdst[1:0]` |

`sbase` is an SGPR pair `s[N:N+1]` holding a 64-bit byte address. `offset` is a 21-bit signed immediate.

---

## FLAT — Unified Memory

Per-lane memory operations. Address is a 64-bit byte address in a VGPR pair `v[N:N+1]`. Active lanes are controlled by the EXEC mask.

| Instruction | Description |
|---|---|
| `FLAT_LOAD_B32 vdst, vaddr [offset:n]` | Load 32-bit word from `vaddr[lane] + offset` into `vdst[lane]` |
| `FLAT_STORE_B32 vaddr, vdata [offset:n]` | Store `vdata[lane]` to `vaddr[lane] + offset` |

---

## Source Operand Classes

| Class | Examples | Notes |
|---|---|---|
| SGPR | `s0`–`s107` | Scalar, single value |
| VGPR | `v0`–`v255` | Vector, one value per lane |
| Inline imm | `0`–`64`, `-1`–`-16` | Encoded in instruction |
| Literal const | `0xDEADBEEF` | 32-bit, follows instruction word |
| Special | `exec_lo`, `exec_hi`, `vcc_lo` | Aliased to specific SGPRs |

---

## Special Registers

| Name | SGPR alias | Description |
|---|---|---|
| `exec_lo` | S126 | Lower 32 bits of EXEC mask |
| `exec_hi` | S127 | Upper 32 bits of EXEC mask |
| `vcc_lo` | S106 | Lower 32 bits of VCC |
| `vcc_hi` | S107 | Upper 32 bits of VCC |
| SCC | — | 1-bit scalar condition code |

---

## Test Coverage

Each instruction is exercised by at least one test in `tests/asm/`:

| Test | Instructions exercised |
|---|---|
| `endpgm.asm` | `S_ENDPGM` |
| `add_one.asm` | `V_MOV_B32`, `V_ADD_NC_U32` |
| `v_add.asm` | `V_MOV_B32`, `V_ADD_NC_U32` |
| `scalar_alu.asm` | `S_MOV_B32`, `S_ADD_U32` |
| `vector_alu.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_NC_U32` (scalar broadcast) |
| `flat_store.asm` | `V_MOV_B32`, `FLAT_STORE_B32` |
| `s_load_b64_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `FLAT_STORE_B32`, `S_LOAD_B64`, `S_WAITCNT` |

---

## Not Yet Implemented (Known Gaps)

- Branch instructions (`S_BRANCH`, `S_CBRANCH_SCC0/1`, etc.)
- `S_LSHL_B32/B64`, `S_AND_B32/B64`, `S_OR_B32/B64`, bitwise scalar ops
- `V_MUL_*`, `V_SUB_*`, `V_AND_B32`, other vector ALU
- `DS_*` LDS instructions
- `BUFFER_*` / `TBUFFER_*` instructions
- `IMAGE_*` instructions
- Export / GDS instructions
- Wavefront divergence / EXEC mask manipulation

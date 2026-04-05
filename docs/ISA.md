# RDNA3 Sail — Supported ISA

Instructions currently implemented in the Sail specification (`spec/`).

---

## SOP2 — Scalar ALU (Two Source)

| Instruction | Description | Flags |
|---|---|---|
| `S_ADD_U32 sdst, ssrc0, ssrc1` | `sdst = ssrc0 + ssrc1` | SCC = carry out |
| `S_SUB_U32 sdst, ssrc0, ssrc1` | `sdst = ssrc0 - ssrc1` | SCC = borrow out |
| `S_AND_B32 sdst, ssrc0, ssrc1` | `sdst = ssrc0 & ssrc1` | SCC = result != 0 |
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
| `S_BRANCH simm16` | PC += simm16 * 4 (unconditional relative branch) |
| `S_CLAUSE imm` | Mark start of a memory clause (no-op in sim) |
| `S_DELAY_ALU imm` | ALU dependency hint (no-op in sim) |
| `S_WAITCNT lgkmcnt(n) / vmcnt(n)` | Wait for memory ops (no-op in sim) |
| `S_ENDPGM` | Halt execution, set halt flag |

---

## VOP1 — Vector ALU (One Source)

Per-lane, gated by the EXEC mask.

| Instruction | Description |
|---|---|
| `V_MOV_B32 vdst, src` | `vdst[lane] = src` for each active lane |

---

## VOP2 — Vector ALU (Two Source)

Per-lane, gated by the EXEC mask.

| Instruction | Description | Flags |
|---|---|---|
| `V_ADD_NC_U32 vdst, src0, src1` | `vdst[lane] = src0[lane] + src1[lane]` (no carry) | — |
| `V_ADD_CO_CI_U32 vdst, src0, src1` | `vdst[lane] = src0[lane] + src1[lane] + VCC[lane]` | VCC = carry out |
| `V_ASHRREV_I32 vdst, src0, src1` | `vdst[lane] = src1[lane] >>> src0[4:0]` (arithmetic) | — |

---

## VOP3 — Vector ALU (Three Source / Extended)

Per-lane, gated by the EXEC mask. VOP3SD variants write a scalar carry destination.

| Instruction | Description | Flags |
|---|---|---|
| `V_ADD_NC_U32 vdst, src0, src1` | Same as VOP2 encoding, no carry | — |
| `V_ADD_CO_U32 vdst, sdst, src0, src1` | `vdst[lane] = src0[lane] + src1[lane]`; carry out → `sdst` | sdst = carry |
| `V_ADD_CO_CI_U32 vdst, sdst, src0, src1, src2` | `vdst[lane] = src0[lane] + src1[lane] + src2[lane]`; carry in from `src2`; carry out → `sdst` | sdst = carry |
| `V_LSHLREV_B64 vdst, src0, src1` | `vdst[lane][63:0] = src1[lane][63:0] << src0[5:0]` | — |
| `V_MAD_U64_U32 vdst, sdst, src0, src1, src2` | `vdst[lane][63:0] = src0[lane] * src1[lane] + src2[lane][63:0]`; overflow → `sdst` | sdst = overflow |

`src` can be a VGPR, SGPR, or inline immediate. SGPR sources are broadcast across all active lanes.

---

## SMEM — Scalar Memory

| Instruction | Description |
|---|---|
| `S_LOAD_B32 sdst, sbase, offset` | Load 32 bits from `sbase[63:0] + offset` into SGPR `sdst` |
| `S_LOAD_B64 sdst, sbase, offset` | Load 64 bits from `sbase[63:0] + offset` into SGPR pair `sdst[1:0]` |

`sbase` is an SGPR pair `s[N:N+1]` holding a 64-bit byte address. `offset` is a 21-bit signed immediate.

---

## FLAT — Unified Memory

Per-lane memory operations. Address is a 64-bit byte address in a VGPR pair `v[N:N+1]`. Active lanes controlled by EXEC mask.

| Instruction | Description |
|---|---|
| `FLAT_LOAD_B32 vdst, vaddr [offset:n]` | Load 32-bit word from `vaddr[lane] + offset` into `vdst[lane]` |
| `FLAT_STORE_B32 vaddr, vdata [offset:n]` | Store `vdata[lane]` to `vaddr[lane] + offset` |
| `FLAT_LOAD_B64 vdst, vaddr [offset:n]` | Load 64-bit word from `vaddr[lane] + offset` into VGPR pair `vdst[lane]` |
| `FLAT_STORE_B64 vaddr, vdata [offset:n]` | Store 64-bit `vdata[lane]` to `vaddr[lane] + offset` |

---

## GLOBAL — Global Memory

Per-lane global memory operations. When `saddr=off` (null, 0x7F), address comes from a VGPR pair; otherwise an SGPR pair provides a 64-bit base and VGPR provides a per-lane 32-bit offset.

| Instruction | Description |
|---|---|
| `GLOBAL_LOAD_B32 vdst, vaddr, saddr [offset:n]` | Load 32-bit word into `vdst[lane]` |
| `GLOBAL_STORE_B32 vaddr, vdata, saddr [offset:n]` | Store `vdata[lane]` to global memory |

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
| `scalar_alu.asm` | `S_MOV_B32`, `S_ADD_U32` |
| `s_and_b32_test.asm` | `S_MOV_B32`, `S_AND_B32` |
| `s_branch.asm` | `S_MOV_B32`, `V_MOV_B32`, `S_BRANCH` |
| `imm_pc.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_NC_U32` |
| `v_add.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_NC_U32` |
| `vector_alu.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_NC_U32` (scalar broadcast) |
| `v_ashrrev_i32_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ASHRREV_I32` |
| `v_add_co_u32_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_CO_U32` |
| `v_add_co_ci_u32_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_ADD_CO_CI_U32` |
| `v_lshlrev_b64_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_LSHLREV_B64` |
| `v_mad_u64_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `V_MAD_U64_U32` |
| `flat_store.asm` | `V_MOV_B32`, `FLAT_STORE_B32`, `FLAT_LOAD_B32` |
| `flat_b64_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `FLAT_STORE_B64`, `FLAT_LOAD_B64` |
| `global_load_store_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `GLOBAL_STORE_B32`, `GLOBAL_LOAD_B32` |
| `s_load_b32_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `FLAT_STORE_B32`, `S_LOAD_B32`, `S_WAITCNT` |
| `s_load_b64_test.asm` | `S_MOV_B32`, `V_MOV_B32`, `FLAT_STORE_B32`, `S_LOAD_B64`, `S_WAITCNT` |
| `read_modify_write.asm` | `S_CLAUSE`, `S_LOAD_B32`, `S_LOAD_B64`, `S_WAITCNT`, `S_AND_B32`, `S_DELAY_ALU`, `V_MAD_U64_U32`, `V_ASHRREV_I32`, `V_LSHLREV_B64`, `V_ADD_CO_U32`, `V_ADD_CO_CI_U32`, `V_ADD_NC_U32`, `GLOBAL_LOAD_B32`, `GLOBAL_STORE_B32` |

---

## Not Yet Implemented (Known Gaps)

- `S_CBRANCH_SCC0/1`, `S_CBRANCH_EXECZ/NZ` — conditional branches
- `S_ADD_I32` — signed scalar add (AST node exists, no decoder/executor)
- `S_LSHL_B32/B64`, `S_OR_B32/B64` — other bitwise scalar ops
- `V_MUL_*`, `V_SUB_*`, `V_AND_B32` — other vector ALU
- `DS_*` — LDS instructions
- `BUFFER_*` / `TBUFFER_*` instructions
- `IMAGE_*` instructions
- Export / GDS instructions
- Wavefront divergence / EXEC mask manipulation

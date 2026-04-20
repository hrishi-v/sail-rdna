register PC :
    QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)
register halt_flag : bits(1)
register error_flag : bits(1)

register EXEC_LO : DWORD
register EXEC_HI : DWORD

register VMCNT : bits(7)
register LGKMCNT : bits(6)

// VMEM pending destination bitmap: bit[i] = 1 means VGPR[i] has a pending
register VMQ_PENDING : vector(256, dec, bits(1))

// VSCNT: vector store credit counter (outstanding VMEM writes).
register VSCNT : bits(6)

// PSQ_SRC_LOCK: Pending Store source-register lock. Each entry holds the
// VGPR index that is the source operand of an in-flight VMEM store. The
// memory write commits synchronously (so intra-wavefront reads see the new
// value via cache forwarding), but the source VGPRs remain locked until
// s_waitcnt_vscnt drains them. Overwriting a locked VGPR is a hazard.
// Sized to 63 — matches the 6-bit VSCNT saturation point.
register PSQ_SRC_LOCK_IDX   : vector(63, dec, bits(8))
register PSQ_SRC_LOCK_COUNT : bits(7)

// VLQ: Vector Load Queue — defers VGPR writes until s_waitcnt vmcnt(0)
register VLQ_DST   : vector(128, dec, bits(8))
register VLQ_VAL   : vector(128, dec, vector(32, dec, DWORD))
register VLQ_COUNT : bits(7)
register VLQ_STAGE : vector(32, dec, DWORD)

// Set while step() is executing an instruction. Stale-read diagnostics
// only fire during instruction execution, not during host/harness probes.
register IN_EXECUTE : bits(1)

register SHARED_BASE : DWORD
register SHARED_LIMIT : DWORD

// M0: special scalar register (encoding 125) used as LDS base offset in DS instructions
register M0 : DWORD

// LDS_BASE: sandbox base address in the unified MEM array for LDS operations.
register LDS_BASE : DWORD

// DS_PENDING: count of ds_read_b32 results already written to VGPRs but
// whose LGKMCNT credit has not yet been drained by s_waitcnt.
register DS_PENDING : bits(5)

// Pending Load Queue to simulate the issue-commit nature of in-flight loads.
register PLQ_DST : vector(16, dec, bits(7))
register PLQ_NDW :
    vector(16, dec, bits(1)) // 0 = 1 dword (b32), 1 = 2 dwords (b64)
register PLQ_VAL :
    vector(16, dec, bits(64)) // fetched value (lower 32 used when ndw=0)
register PLQ_COUNT :
    bits(5)

val EXTZ : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTZ(m, v) = sail_zero_extend(v, m)

val EXTS : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTS(m, v) = sail_sign_extend(v, m)

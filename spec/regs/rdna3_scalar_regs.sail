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
// VMEM load that has not yet been drained by s_waitcnt vmcnt(0).
register VMQ_PENDING : vector(256, dec, bits(1))

// Set while step() is executing an instruction. Stale-read diagnostics
// only fire during instruction execution, not during host/harness probes.
register IN_EXECUTE : bits(1)

register SHARED_BASE : DWORD
register SHARED_LIMIT : DWORD

// M0: special scalar register (encoding 124) used as LDS base offset in DS instructions
register M0 : DWORD

// LDS_BASE: sandbox base address in the unified MEM array for LDS operations.
// Default 0x8000 keeps LDS in the upper half of the 64 KB MEM array,
// well above code/SMEM regions that live near address 0.
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
    bits(5) // number of entries in the queue (0..16)
register PLQ_READY : vector(16, dec, bits(16))
register CYCLE_COUNT : bits(16)

val EXTZ : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTZ(m, v) = sail_zero_extend(v, m)

val EXTS : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTS(m, v) = sail_sign_extend(v, m)

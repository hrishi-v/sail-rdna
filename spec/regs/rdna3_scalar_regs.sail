register PC :
    QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)
register halt_flag : bits(1)
register error_flag : bits(1)

register EXEC_LO : DWORD
register EXEC_HI : DWORD

register VMCNT : bits(6)
register LGKMCNT : bits(6)

register SHARED_BASE : DWORD
register SHARED_LIMIT : DWORD

// Pending Load Queue to simulate the issue-commit nature of in-flight loads.

register PLQ_DST   : vector(16, dec, bits(7))
register PLQ_NDW   : vector(16, dec, bits(1))   // 0 = 1 dword (b32), 1 = 2 dwords (b64)
register PLQ_VAL   : vector(16, dec, bits(64))  // fetched value (lower 32 used when ndw=0)
register PLQ_COUNT : bits(5)                     // number of entries in the queue (0..16)
register PLQ_READY : vector(16, dec, bits(16))
register CYCLE_COUNT : bits(16)

val EXTZ : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTZ(m, v) = sail_zero_extend(v, m)

val EXTS : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTS(m, v) = sail_sign_extend(v, m)

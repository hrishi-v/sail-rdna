register PC : QWORD // 48-bits used, 2 LSBs 0
register SGPR : vector(108, dec, DWORD)
register SCC : bits(1)
register halt_flag : bits(1)

register EXEC_LO : DWORD
register EXEC_HI : DWORD

register VMCNT : bits(6)
register LGKMCNT : bits(6)

register SHARED_BASE  : DWORD
register SHARED_LIMIT : DWORD

val EXTZ : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTZ(m, v) = sail_zero_extend(v, m)

val EXTS : forall 'n 'm, 'm >= 'n. (implicit('m), bits('n)) -> bits('m)
function EXTS(m, v) = sail_sign_extend(v, m)
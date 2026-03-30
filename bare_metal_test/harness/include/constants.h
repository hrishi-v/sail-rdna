#define WAVE_SIZE 32
#define MEM_BUF_SIZE 64  // 64 ints = 256 bytes, enough for all memory tests

#ifndef NUM_VGPRS
#define NUM_VGPRS 1
#endif

#ifndef NUM_SGPRS
#define NUM_SGPRS 0
#endif

#ifndef VGPR_INDICES
#define VGPR_INDICES {5}
#endif

#ifndef SGPR_INDICES
#define SGPR_INDICES {}
#endif
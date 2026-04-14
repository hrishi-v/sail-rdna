#include <hip/hip_runtime.h>

extern "C" __global__
__attribute__((amdgpu_num_vgpr(64)))
__attribute__((amdgpu_lds_size(4096)))   // 4 KB LDS — required for ds_read/write_b32 experiments
void asm_kernel(int* vgpr_out, int* sgpr_out, int* mem_buf) {
    __shared__ volatile uint32_t lds_pool[1024];

    // Force LDS liveness: a real C++ store that LLVM cannot eliminate.
    // threadIdx.x is a hardware register read (v0 at kernel entry), so the
    // store is divergent across lanes and cannot be proved dead.
    lds_pool[threadIdx.x] = 0xdeadbeef;

    unsigned int vgpr_lo = (unsigned int)((unsigned long long)vgpr_out & 0xFFFFFFFFULL);
    unsigned int vgpr_hi = (unsigned int)((unsigned long long)vgpr_out >> 32);

    unsigned int sgpr_lo = (unsigned int)((unsigned long long)sgpr_out & 0xFFFFFFFFULL);
    unsigned int sgpr_hi = (unsigned int)((unsigned long long)sgpr_out >> 32);

    unsigned int mem_lo  = (unsigned int)((unsigned long long)mem_buf  & 0xFFFFFFFFULL);
    unsigned int mem_hi  = (unsigned int)((unsigned long long)mem_buf  >> 32);

    asm volatile (
        "s_mov_b32 s20, %0\n\t"
        "s_mov_b32 s21, %1\n\t"
        "s_mov_b32 s22, %2\n\t"
        "s_mov_b32 s23, %3\n\t"
        "s_mov_b32 s24, %4\n\t"
        "s_mov_b32 s25, %5\n\t"

        #include TEST_INC
        #include DUMP_INC

        :
        : "s"(vgpr_lo), "s"(vgpr_hi),
          "s"(sgpr_lo), "s"(sgpr_hi),
          "s"(mem_lo), "s"(mem_hi)
        : "v30", "v31", "v32", "v33",
          "s20", "s21", "s22", "s23", "s24", "s25",
          "vcc", "memory"
    );
}
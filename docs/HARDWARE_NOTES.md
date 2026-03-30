# Sail Specification vs Bare-Metal

## Register Initialisation
Sail zeros all VGPRs/SGPRs before execution. Real hardware does not. This was surfaced when a vector add instruction used an uninitialised v1 in the test file, as the bare metal and the specification did not concur.

## Vector-Scalar cache coherency 

My Sail specification has a unified flat memory (so far). Real hardware has separate vector (VMEM) and scalar (K-cache) caches. A `flat_store_b32` from the vector path is not visible to a subsequent `s_load_b64` without an explicit `s_dcache_inv`. Sail's model elides this entirely. 

On RDNA3 there are multiple cache levels on the memory path, slightly different for vector and scalar values:

  - Vector ALU → GL0 (vector L1) → GL1 (shared L2) → memory
  - Scalar ALU →    K-cache       → GL1 (shared L2) → memory

When we execute the `flat_store_b32` the write goes through the memory hierarchy (landing in Vector L1, L2 and Global Memory). The scalar path has similar. The use of the assembly instruction will have the K-cache be completely discarded, such that the following instructions will load the result of the store from shared L2 cache.

## EXEC mask initialisation

Sail initialises exec_lo to 0 (all lanes inactive) because registers are zeroed. Real hardware launches kernels with EXEC = all-ones. This arose when some tests were missing s_mov_b32
exec_lo, -1, to activate all lanes!
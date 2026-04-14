; ds_read_b32_optimal.asm
; TEST_LDS_OPTIMAL: Each lane reads from a unique bank (stride-1 = 4 bytes/lane).
;
; Bank math:
;   lane 0 → addr 0x000 → bank (0/4)%32 = 0
;   lane 1 → addr 0x004 → bank (4/4)%32 = 1
;   lane 2 → addr 0x008 → bank (8/4)%32 = 2
;   ...
;   lane 31 → addr 0x07C → bank (124/4)%32 = 31
;
; All 32 banks hit exactly once → NO bank conflict.
; Expected Sail diagnostic: NONE (max_hits == 1).
;
; Strategy:
;   Without v_mbcnt_lo_u32_b32 in the model, we use EXEC-mask walking:
;   enable one lane at a time and v_mov_b32 its address into v2.
;   Then restore full exec and issue ds_read_b32 with all 32 unique addrs.
;
; Pre-populate LDS: write 0xDEADBEEF to each address via flat_store_b32
; at LDS_BASE + lane_addr (0x8000 + lane*4).

; ── 1. Pre-populate LDS region with known data ────────────────────────────
; Write 0xDEADBEEF to addresses 0x8000..0x807C (32 DWORDs)
s_mov_b32 exec_lo, 1         ; single lane for setup
v_mov_b32 v10, 0xDEADBEEF    ; data to write

; Use flat_store to plant data at each LDS sandbox address.
; LDS_BASE = 0x8000, so MEM[0x8000 + lane*4] for lane 0..31.
v_mov_b32 v1, 0x00000000     ; addr_hi = 0

v_mov_b32 v0, 0x00008000     ; addr 0x8000 (lane 0)
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008004     ; addr 0x8004 (lane 1)
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008008     ; addr 0x8008 (lane 2)
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000800C     ; addr 0x800C (lane 3)
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008010
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008014
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008018
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000801C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008020
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008024
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008028
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000802C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008030
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008034
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008038
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000803C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008040
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008044
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008048
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000804C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008050
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008054
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008058
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000805C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008060
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008064
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008068
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000806C
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008070
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008074
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x00008078
flat_store_b32 v[0:1], v10
v_mov_b32 v0, 0x0000807C
flat_store_b32 v[0:1], v10
s_waitcnt vmcnt(0)

; ── 2. Set per-lane addresses in v2 via EXEC walking ──────────────────────
; Each lane gets addr = lane_id * 4 (stride-1 DWORD).

s_mov_b32 exec_lo, 0x00000001    ; lane 0
v_mov_b32 v2, 0x00000000         ; addr = 0
s_mov_b32 exec_lo, 0x00000002    ; lane 1
v_mov_b32 v2, 0x00000004         ; addr = 4
s_mov_b32 exec_lo, 0x00000004    ; lane 2
v_mov_b32 v2, 0x00000008         ; addr = 8
s_mov_b32 exec_lo, 0x00000008    ; lane 3
v_mov_b32 v2, 0x0000000C         ; addr = 12
s_mov_b32 exec_lo, 0x00000010    ; lane 4
v_mov_b32 v2, 0x00000010
s_mov_b32 exec_lo, 0x00000020    ; lane 5
v_mov_b32 v2, 0x00000014
s_mov_b32 exec_lo, 0x00000040    ; lane 6
v_mov_b32 v2, 0x00000018
s_mov_b32 exec_lo, 0x00000080    ; lane 7
v_mov_b32 v2, 0x0000001C
s_mov_b32 exec_lo, 0x00000100    ; lane 8
v_mov_b32 v2, 0x00000020
s_mov_b32 exec_lo, 0x00000200    ; lane 9
v_mov_b32 v2, 0x00000024
s_mov_b32 exec_lo, 0x00000400    ; lane 10
v_mov_b32 v2, 0x00000028
s_mov_b32 exec_lo, 0x00000800    ; lane 11
v_mov_b32 v2, 0x0000002C
s_mov_b32 exec_lo, 0x00001000    ; lane 12
v_mov_b32 v2, 0x00000030
s_mov_b32 exec_lo, 0x00002000    ; lane 13
v_mov_b32 v2, 0x00000034
s_mov_b32 exec_lo, 0x00004000    ; lane 14
v_mov_b32 v2, 0x00000038
s_mov_b32 exec_lo, 0x00008000    ; lane 15
v_mov_b32 v2, 0x0000003C
s_mov_b32 exec_lo, 0x00010000    ; lane 16
v_mov_b32 v2, 0x00000040
s_mov_b32 exec_lo, 0x00020000    ; lane 17
v_mov_b32 v2, 0x00000044
s_mov_b32 exec_lo, 0x00040000    ; lane 18
v_mov_b32 v2, 0x00000048
s_mov_b32 exec_lo, 0x00080000    ; lane 19
v_mov_b32 v2, 0x0000004C
s_mov_b32 exec_lo, 0x00100000    ; lane 20
v_mov_b32 v2, 0x00000050
s_mov_b32 exec_lo, 0x00200000    ; lane 21
v_mov_b32 v2, 0x00000054
s_mov_b32 exec_lo, 0x00400000    ; lane 22
v_mov_b32 v2, 0x00000058
s_mov_b32 exec_lo, 0x00800000    ; lane 23
v_mov_b32 v2, 0x0000005C
s_mov_b32 exec_lo, 0x01000000    ; lane 24
v_mov_b32 v2, 0x00000060
s_mov_b32 exec_lo, 0x02000000    ; lane 25
v_mov_b32 v2, 0x00000064
s_mov_b32 exec_lo, 0x04000000    ; lane 26
v_mov_b32 v2, 0x00000068
s_mov_b32 exec_lo, 0x08000000    ; lane 27
v_mov_b32 v2, 0x0000006C
s_mov_b32 exec_lo, 0x10000000    ; lane 28
v_mov_b32 v2, 0x00000070
s_mov_b32 exec_lo, 0x20000000    ; lane 29
v_mov_b32 v2, 0x00000074
s_mov_b32 exec_lo, 0x40000000    ; lane 30
v_mov_b32 v2, 0x00000078
s_mov_b32 exec_lo, 0x80000000    ; lane 31
v_mov_b32 v2, 0x0000007C

; ── 3. Restore full wave and issue ds_read_b32 ────────────────────────────
s_mov_b32 exec_lo, -1            ; all 32 lanes active
ds_read_b32 v0, v2               ; each lane reads from its unique bank
s_waitcnt lgkmcnt(0)

; Expected: v0[lane] = 0xDEADBEEF for all lanes, NO diagnostic printed.
s_endpgm

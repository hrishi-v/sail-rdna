; ds_read_b32_conflict.asm
; TEST_LDS_CONFLICT: All 32 lanes read from the same address → 32-way conflict.
;
; Bank math:
;   stride = 128 bytes/lane → but here ALL lanes share addr 0x000.
;   Every lane: addr = 0x000 → bank = (0/4) % 32 = 0
;   All 32 lanes hit bank 0 → 32-way bank conflict.
;
; Expected Sail diagnostic:
;   [DIAG] ds_read_b32: 32-way bank conflict on bank 0.
;   Expected replay penalty: ~31 extra cycles
;
; Strategy:
;   v_mov_b32 with an immediate writes the SAME value to all active lanes.
;   So v_mov_b32 v2, 0x0 gives every lane address 0 → all hit bank 0.
;   Pre-populate MEM[LDS_BASE + 0] = 0xDEADBEEF via flat_store.

; ── 1. Pre-populate LDS at address 0 (LDS_BASE + 0 = 0x8000) ─────────────
s_mov_b32 exec_lo, -1            ; all lanes active
v_mov_b32 v0, 0x00008000         ; addr_lo = LDS_BASE
v_mov_b32 v1, 0x00000000         ; addr_hi = 0
v_mov_b32 v10, 0xDEADBEEF        ; data to write
flat_store_b32 v[0:1], v10
s_waitcnt vmcnt(0)

; ── 2. Set all lanes to address 0 (uniform → 32-way bank conflict) ────────
v_mov_b32 v2, 0x00000000         ; every lane gets addr = 0

; ── 3. Issue ds_read_b32 — should trigger 32-way conflict diagnostic ──────
ds_read_b32 v0, v2               ; 32 lanes all reading bank 0
s_waitcnt lgkmcnt(0)

; Expected: v0[all lanes] = 0xDEADBEEF, diagnostic printed by Sail model.
s_endpgm

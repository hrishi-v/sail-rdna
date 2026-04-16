default Order dec

$include <prelude.sail>

$include "rdna3_types.sail"
$include "rdna3_const.sail"

$include "rdna3_ast.sail"
$include "rdna3_imem.sail"

$include "regs/rdna3_scalar_regs.sail"
$include "regs/rdna3_scalar_reg_ops.sail"

$include "regs/rdna3_vector_regs.sail"
$include "regs/rdna3_vector_reg_ops.sail"

$include "decode/rdna3_flat_decode.sail"
$include "decode/rdna3_s_decode.sail"
$include "decode/rdna3_v_decode.sail"
$include "decode/rdna3_ds_decode.sail"
$include "decode/rdna3_mubuf_decode.sail"
$include "decode/rdna3_decode.sail"

$include "execute/rdna3_flat_execute.sail"
$include "execute/rdna3_s_execute.sail"
$include "execute/rdna3_v_execute.sail"
$include "execute/rdna3_ds_execute.sail"
$include "execute/rdna3_mubuf_execute.sail"
$include "execute/rdna3_execute.sail"

val step : unit -> unit
function step () = {
    let instr = fetch_inst(PC);
    PC = PC + 4;
    let ast_node = decode(instr);
    IN_EXECUTE = 0b1;
    execute(ast_node);
    IN_EXECUTE = 0b0;
    CYCLE_COUNT = CYCLE_COUNT + 1
}

val get_pc : unit -> QWORD
function get_pc () = { PC }

val get_sgpr : sgpr_idx -> DWORD
function get_sgpr id = {
    rSGPR(id)
}

val set_pc : QWORD -> unit
function set_pc start_addr = {
    PC = start_addr
}

val reset_vmcnt : unit -> unit
function reset_vmcnt () = {
    VMCNT = 0b0000000
}

val reset_vmq : unit -> unit
function reset_vmq () = {
    foreach (i from 0 to 255) {
        VMQ_PENDING[i] = 0b0
    }
}

val reset_lgkmcnt : unit -> unit
function reset_lgkmcnt () = {
    LGKMCNT = 0b000000
}

val reset_pending_load_queue : unit -> unit
function reset_pending_load_queue () = {
    PLQ_COUNT = 0b00000;
    CYCLE_COUNT = 0x0000
}

val reset_halt_flag : unit -> unit
function reset_halt_flag () = {
    halt_flag = 0b0
}

val reset_ds_pending : unit -> unit
function reset_ds_pending () = {
    DS_PENDING = 0b00000
}

val reset_vscnt : unit -> unit
function reset_vscnt () = {
    VSCNT = 0b000000
}

val reset_vlq : unit -> unit
function reset_vlq () = {
    VLQ_COUNT = 0b0000000
}

// LDS_BASE default: 0x8000 (32 KB mark in the 64 KB MEM array).
// Sandboxes LDS away from code/SMEM regions near address 0.
val reset_lds_base : unit -> unit
function reset_lds_base () = {
    LDS_BASE = 0x00008000
}

val set_m0 : DWORD -> unit
function set_m0 value = {
    M0 = value
}

val get_m0 : unit -> DWORD
function get_m0 () = { M0 }

val set_lds_base : DWORD -> unit
function set_lds_base value = {
    LDS_BASE = value
}

val get_lds_base : unit -> DWORD
function get_lds_base () = { LDS_BASE }

val get_error_flag : unit -> bool
function get_error_flag () = {
    error_flag == 0b1
}

val reset_error_flag : unit -> unit
function reset_error_flag () = {
    error_flag = 0b0
}

val main : unit -> unit
function main () = {
    let dummy_addr : QWORD = 0x0000000000000000;
    let dummy_data32 : DWORD = 0x00000000;
    let dummy_data8 : bits(8) = 0x00;

    let _ = get_pc();
    let _ = get_sgpr(0b0000000);
    let _ = get_error_flag();
    reset_error_flag();
    set_pc(dummy_addr);

    IN_EXECUTE = 0b0;
    reset_vmcnt();
    reset_vmq();
    reset_lgkmcnt();
    reset_pending_load_queue();
    reset_halt_flag();
    reset_ds_pending();
    reset_lds_base();
    reset_vscnt();
    reset_vlq();

    write_mem_8(dummy_addr, dummy_data8);
    write_mem_32(dummy_addr, dummy_data32);
    let _ = read_mem_32(dummy_addr);
    let _ = get_halt_flag();

    step()
}

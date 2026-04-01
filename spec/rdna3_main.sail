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
$include "decode/rdna3_decode.sail"

$include "execute/rdna3_flat_execute.sail"
$include "execute/rdna3_s_execute.sail"
$include "execute/rdna3_v_execute.sail"
$include "execute/rdna3_execute.sail"

val step : unit -> unit
function step () = {
    let instr = fetch_inst(PC);
    PC = PC + 4;
    let ast_node = decode(instr);
    execute(ast_node)
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
    VMCNT = 0b000000
}

val reset_lgkmcnt : unit -> unit
function reset_lgkmcnt () = {
    LGKMCNT = 0b000000
}

val reset_halt_flag : unit -> unit
function reset_halt_flag () = {
    halt_flag = 0b0
}

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

    reset_vmcnt();
    reset_lgkmcnt();
    reset_halt_flag();

    write_mem_8(dummy_addr, dummy_data8);
    write_mem_32(dummy_addr, dummy_data32);
    let _ = read_mem_32(dummy_addr);
    let _ = get_halt_flag();

    step()
}

default Order dec

$include <prelude.sail>

$include "rdna3_types.sail"
$include "rdna3_const.sail"

$include "rdna3_scalar_regs.sail"
$include "rdna3_scalar_reg_ops.sail"

$include "rdna3_vector_regs.sail"
$include "rdna3_vector_reg_ops.sail"


$include "rdna3_imem.sail"
$include "rdna3_ast.sail"

$include "decode/rdna3_s_decode.sail"
$include "decode/rdna3_decode.sail"

$include "execute/rdna3_s_execute.sail"
$include "execute/rdna3_execute.sail"

$include "rdna3_tests.sail"

val sail_test_main : unit -> unit
function sail_test_main() = {
    // --- C++ HOOK EXPORTS ---
    // These harmless calls force Sail to compile these functions into C
    // so our C++ motherboard can link to them without DCE destroying them.
    set_pc(PC); 
    write_mem_8(0x0000000000000000, 0x00);
    let _dummy = get_halt_flag();
    // ------------------------

    print("RDNA3 Emulator Starting...\n");

    // ------------------------------------------------
    // SELECT YOUR TEST HERE
    // ------------------------------------------------
    load_test_add();
    load_test_sub();
    load_test_cmp_select();
    load_test_shift64();
    load_end_pgm();
    // ------------------------------------------------
}

val main : unit -> unit
function main() = {
    sail_test_main()
}
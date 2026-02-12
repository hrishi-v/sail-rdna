default Order dec

$include <prelude.sail>

$include "rdna3_types.sail"
$include "rdna3_const.sail"
$include "rdna3_regs.sail"
$include "rdna3_imem.sail"
$include "rdna3_ast.sail"

$include "decode/rdna3_s_decode.sail"
$include "decode/rdna3_decode.sail"
$include "execute/rdna3_s_execute.sail"
$include "execute/rdna3_execute.sail"

$include "rdna3_tests.sail"

val main : unit -> unit
function main() = {
    print("RDNA3 Emulator Starting...\n");

    // ------------------------------------------------
    // SELECT YOUR TEST HERE
    // ------------------------------------------------
    load_test_add();
    // load_test_sub();
    // ------------------------------------------------
}
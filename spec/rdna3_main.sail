default Order dec

$include <prelude.sail>

$include "rdna3_types.sail"
$include "rdna3_regs.sail"
$include "rdna3_imem.sail"
$include "rdna3_ast.sail"
$include "decode/rdna3_s_decode.sail"
$include "decode/rdna3_decode.sail"


val main : unit -> unit
function main() = {
    PC = 0x0000000000000000;
    wVCC(0xFFFFFFFFFFFFFFFF);

    print("RDNA3 Emulator Initialized.\n");
    write_mem_32(PC, 0xAABBCCDD);
    print("Loaded Instruction 0xAABBCCDD into memory.\n");
    let inst : DWORD = fetch_inst(PC);
    print_bits("Fetched : ", inst);

    if (inst == 0xAABBCCDD) then {
        print("SUCCESS: Memory Fetch is working!\n");
    } else {
        print("ERROR: Endianness mismatch or fetch logic failed.\n");
    }

}
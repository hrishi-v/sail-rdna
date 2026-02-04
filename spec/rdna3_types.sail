default Order dec
$include <prelude.sail>

type bits32 = bits(32)
type bits64 = bits(64)
type reg_id = bits(8)

union operand = {
    Op_Reg : reg_id,
    Op_Imm32 : bits32
}
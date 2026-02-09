default Order dec
$include <prelude.sail>

type SHORT_LENGTH : Int = 16
type DWORD_LENGTH : Int = 32
type QWORD_LENGTH : Int = 64

type BYTE = bits(8)
type SHORT = bits(SHORT_LENGTH)
type DWORD = bits(DWORD_LENGTH)
type QWORD = bits(QWORD_LENGTH)
 
// Register Addressing
type reg_id = bits(8)

union operand = {
    Op_Reg : reg_id,
    Op_Imm32 : DWORD
}
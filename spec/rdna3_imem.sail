register MEM : vector(65536, dec, bits(8))

val fetch_inst : QWORD -> DWORD
function fetch_inst(addr) = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if (a + 3 < 65536) then {
        MEM[a+3] @ MEM[a+2] @ MEM[a+1] @ MEM[a]
    } else {
        0x00000000
    }
}


val read_mem_32 : QWORD -> DWORD
function read_mem_32(addr) = {
    let a_bits = addr[15..0]; 
    let a = unsigned(a_bits);

    if (a + 3 < 65536) then {
        MEM[a+3] @ MEM[a+2] @ MEM[a+1] @ MEM[a]
    } else {
        0x00000000
    }
}

val write_mem_32 : (QWORD, DWORD) -> unit
function write_mem_32(addr, data) = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if (a + 3 < 65536) then {
        MEM[a]   = data[7..0];
        MEM[a+1] = data[15..8];
        MEM[a+2] = data[23..16];
        MEM[a+3] = data[31..24];
    }
}

val write_mem_8 : (QWORD, bits(8)) -> unit
function write_mem_8(addr, data) = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if (a < 65536) then {
        MEM[a] = data
    }
}
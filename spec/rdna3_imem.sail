register MEM : vector(65536, dec, bits(8))

val fetch_inst : QWORD -> DWORD
function fetch_inst addr = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if a + 3 < 65536 then {
        MEM[a + 3] @ MEM[a + 2] @ MEM[a + 1] @ MEM[a]
    } else { 0x00000000 }
}

val read_mem_32 : QWORD -> DWORD
function read_mem_32 addr = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if a + 3 < 65536 then {
        MEM[a + 3] @ MEM[a + 2] @ MEM[a + 1] @ MEM[a]
    } else { 0x00000000 }
}

val read_mem_64 : QWORD -> QWORD
function read_mem_64 addr = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if a + 7 < 65536 then {
        MEM[a + 7] @ MEM[a + 6] @ MEM[a + 5] @ MEM[a+4] @ MEM[a + 3] @ MEM[a + 2] @ MEM[a + 1] @ MEM[a]
    } else { 0x0000000000000000 }
}

val write_mem_32 : (QWORD, DWORD) -> unit
function write_mem_32(addr, data) = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if a + 3 < 65536 then {
        MEM[a] = data[7..0];
        MEM[a + 1] = data[15..8];
        MEM[a + 2] = data[23..16];
        MEM[a + 3] = data[31..24]
    }
}

val write_mem_64 : (QWORD, QWORD) -> unit
function write_mem_64(addr, data) = {
    let a_bits = addr[15..0];
    let a = unsigned(a_bits);

    if a + 7 < 65536 then {
        MEM[a]     = data[7..0];
        MEM[a + 1] = data[15..8];
        MEM[a + 2] = data[23..16];
        MEM[a + 3] = data[31..24];
        MEM[a + 4] = data[39..32];
        MEM[a + 5] = data[47..40];
        MEM[a + 6] = data[55..48];
        MEM[a + 7] = data[63..56]
    } else {
      0x0000000000000000
    }
}
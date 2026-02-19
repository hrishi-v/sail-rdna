val step : unit -> unit
function step() = {
    let inst_bits : bits(32) = fetch_inst(PC);
    
    let inst_ast : ast = decode(inst_bits);
    
    execute(inst_ast);
    
    PC = PC + 4;
}


val load_test_add : unit -> unit
function load_test_add() = {
    print("\ns_add_u32 s0, s1, s2 test!\n");
    write_mem_32(0x0000000000000100, 0x80000201); // Load instruction
    
    // Set up registers
    wSGPR(0b0000001, 0x0000000A);
    wSGPR(0b0000010, 0x00000014);

    PC = 0x0000000000000100;
    step();
    
    let res = read_scalar_source(0b00000000);
    
    if (res == 0x0000001E) then {
        print_bits("[PASS] Result: ", res);
    } else {
        print_bits("[FAIL] Result: ", res);
    };

    print("\n");
}

val load_test_sub : unit -> unit
function load_test_sub() = {
    // Hex: 10(Prefix) 11111(SOP2) ...
    // Let's say s_sub_u32 s3, s4, s5 -> 0x80010504
    print("\ns_sub_u32 s3, s4, s5 test!\n");
    write_mem_32(0x0000000000000100, 0x80830504);

    // Set up registers
    wSGPR(0b0000100, 0x00000014); // 20
    wSGPR(0b0000101, 0x0000000A); // 10

    PC = 0x0000000000000100;
    step();
    
    let res = read_scalar_source(0b00000011);
    
    if (res == 0x0000000A) then {
        print_bits("[PASS] Result: ", res);
    } else {
        print_bits("[FAIL] Result: ", res);
    };

    print("\n");
}
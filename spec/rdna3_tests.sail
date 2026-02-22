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

val load_test_cmp_select : unit -> unit
function load_test_cmp_select() = {
    print("\ns_cmp_eq_i32 + s_cselect_b32 test!\n");
    
    // Set up registers
    wSGPR(0b0000000, 0x0000000A);
    wSGPR(0b0000001, 0x0000000A);
    
    wSGPR(0b0000010, 0x00000063);
    wSGPR(0b0000011, 0x0000002A);

    // 1. s_cmp_eq_i32 s0, s1
    // Prefix: 101111111 (SOPC) | OP: 0000000 (0) | SSRC1: 00000001 (s1) | SSRC0: 00000000 (s0)
    // Binary: 1011 1111 1000 0000 0000 0001 0000 0000 -> 0xBF800100
    write_mem_32(0x0000000000000100, 0xBF000100); 

    // 2. s_cselect_b32 s4, s2, s3
    // Prefix: 10 (SOP2) | OP: 0001010 (Let's say OP is 10) | SDST: 0000100 (s4) | SSRC1: 00000011 (s3) | SSRC0: 00000010 (s2)
    // Binary: 1000 0101 0000 0100 0000 0011 0000 0010 -> 0x85040302
    write_mem_32(0x0000000000000104, 0x98040302);

    PC = 0x0000000000000100;
    step();
    
    step();
    
    // Check Result
    let res = read_scalar_source(0b00000100); // Read s4
    
    if (res == 0x00000063) then {
        print_bits("[PASS] CSELECT picked True (99): ", res);
    } else {
        print_bits("[FAIL] CSELECT failed, got: ", res);
    };
    print("\n");
}

val load_test_shift64 : unit -> unit
function load_test_shift64() = {
    print("\ns_mov_b64 + s_lshr_b64 test!\n");
    
    // Hardcode 64-bit value 0x00000000_00000100 into s[0:1] manually for testing the shift
    wSGPR(0b0000000, 0x00000100); // s0 (Lower)
    wSGPR(0b0000001, 0x00000000); // s1 (Upper)
    
    // Hardcode the shift amount into s2
    wSGPR(0b0000010, 0x00000004); // s2 = 4
    
    // s_lshr_b64 s[4:5], s[0:1], s2
    // Prefix: 10 (SOP2) | OP: 0011111 (Let's say OP is 31 / 0x1F) | SDST: 0000100 (s4) | SSRC1: 00000010 (s2) | SSRC0: 00000000 (s0)
    // Binary: 1000 0111 1100 0100 0000 0010 0000 0000 -> 0x87C40200
    write_mem_32(0x0000000000000100, 0x85840200);

    PC = 0x0000000000000100;
    step();
    
    // Check Result: After shift, lower 32 bits (s4) should be 0x10. Upper (s5) should be 0x0.
    let res_lower = read_scalar_source(0b00000100); // Read s4
    let res_upper = read_scalar_source(0b00000101); // Read s5
    
    if (res_lower == 0x00000010 & res_upper == 0x00000000) then {
        print_bits("[PASS] LSHR result correct: ", res_lower);
    } else {
        print_bits("[FAIL] LSHR failed, lower bits got: ", res_lower);
    };
    print("\n");
}

val load_end_pgm : unit -> unit
function load_end_pgm() = {
    print("\nend_pgm test!\n");
    write_mem_32(0x0000000000000100, 0xBFB00000);
    PC = 0x0000000000000100;
    step();
}
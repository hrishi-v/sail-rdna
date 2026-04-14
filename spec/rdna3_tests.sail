val load_test_add : unit -> unit
function load_test_add () = {
    print("\ns_add_u32 s0, s1, s2 test!\n");
    write_mem_32(0x0000000000000100, 0x80000201); // Load instruction

    // Set up registers
    wSGPR(0b0000001, 0x0000000A);
    wSGPR(0b0000010, 0x00000014);

    PC = 0x0000000000000100;
    step();

    let res = read_common_source(unsigned(0b00000000));

    if res == 0x0000001E then {
        print_bits("[PASS] Result: ", res)
    } else {
        print_bits("[FAIL] Result: ", res)
    };

    print("\n")
}

val load_test_sub : unit -> unit
function load_test_sub () = {
    // Hex: 10(Prefix) 11111(SOP2) ...
    // s_sub_u32 s3, s4, s5 -> 0x80010504
    print("\ns_sub_u32 s3, s4, s5 test!\n");
    write_mem_32(0x0000000000000100, 0x80830504);

    // Set up registers
    wSGPR(0b0000100, 0x00000014); // 20
    wSGPR(0b0000101, 0x0000000A); // 10

    PC = 0x0000000000000100;
    step();

    let res = read_common_source(unsigned(0b00000011));

    if res == 0x0000000A then {
        print_bits("[PASS] Result: ", res)
    } else {
        print_bits("[FAIL] Result: ", res)
    };

    print("\n")
}

val load_test_cmp_select : unit -> unit
function load_test_cmp_select () = {
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
    let res = read_common_source(unsigned(0b00000100)); // Read s4

    if res == 0x00000063 then {
        print_bits("[PASS] CSELECT picked True (99): ", res)
    } else {
        print_bits("[FAIL] CSELECT failed, got: ", res)
    };
    print("\n")
}

val load_test_shift64 : unit -> unit
function load_test_shift64 () = {
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
    let res_lower = read_common_source(unsigned(0b00000100)); // Read s4
    let res_upper = read_common_source(unsigned(0b00000101)); // Read s5

    if res_lower == 0x00000010 & res_upper == 0x00000000 then {
        print_bits("[PASS] LSHR result correct: ", res_lower)
    } else {
        print_bits("[FAIL] LSHR failed, lower bits got: ", res_lower)
    };
    print("\n")
}

val load_end_pgm : unit -> unit
function load_end_pgm () = {
    print("\nend_pgm test!\n");
    write_mem_32(0x0000000000000100, 0xBFB00000);
    PC = 0x0000000000000100;
    step()
}

val load_test_flat_load : unit -> unit
function load_test_flat_load () = {
    print("\nflat_load_b32 v2, v[0:1] test!\n");

    SHARED_BASE = 0x00001000;
    SHARED_LIMIT = 0x00001FFF;

    wVGPR(0b00000000, 0b00000, 0x00002000); // v0 = 0x2000
    wVGPR(0b00000001, 0b00000, 0x00000000); // v1 = 0x0000

    EXEC_LO = 0x00000001;

    VMCNT = 0b0000000;
    LGKMCNT = 0b000000;

    write_mem_32(0x0000000000002000, 0xDEADBEEF);

    // Instruction: flat_load_b32 v2, v[0:1]
    // Low DWORD: 0xDC500000 (Prefix: 110111, OP: 0010100, SEG: 0)
    // High DWORD: 0x02000000 (VDST: 2, ADDR: 0)
    write_mem_32(0x0000000000000100, 0xDC500000); // First 32 bits
    write_mem_32(0x0000000000000104, 0x02000000); // Second 32 bits

    PC = 0x0000000000000100;
    step();

    let res = rVGPR(0b00000010, 0b00000); // Read v2, Lane 0

    if res == 0xDEADBEEF & VMCNT == 0b00000001 & LGKMCNT == 0b000000 then {
        print("\n[PASS] FLAT Load successful!\n");
        print_bits("Data: ", res);
        print("VMCNT correctly incremented to 1 for Global Memory.")
    } else {
        print("\n[FAIL] FLAT Load failed.");
        print_bits("Expected 0xDEADBEEF, Got: ", res);
        print_bits("Expected VMCNT 1, Got: ", VMCNT)
    };

    print("\n")
}

val load_test_flat_store : unit -> unit
function load_test_flat_store () = {
    print("\nflat_store_b32 v[0:1], v2 test!\n");
    SHARED_BASE = 0x00001000;
    SHARED_LIMIT = 0x00001FFF;

    // Pointing to 0x00001008 (Falls inside the SHARED aperture!)
    wVGPR(0b00000000, 0b00000, 0x00001008); // v0 = 0x1008
    wVGPR(0b00000001, 0b00000, 0x00000000); // v1 = 0x0000

    wVGPR(0b00000010, 0b00000, 0xCAFEBABE); // v2 = 0xCAFEBABE

    EXEC_LO = 0x00000001;

    // Reset counters before the test
    VMCNT = 0b0000000;
    LGKMCNT = 0b000000;
    write_mem_32(0x0000000000001008, 0x00000000);

    write_mem_32(0x0000000000000100, 0xDC680000);
    write_mem_32(0x0000000000000104, 0x00000200);

    PC = 0x0000000000000100;

    step();

    let mem_res = read_mem_32(0x0000000000001008);

    if mem_res == 0xCAFEBABE & LGKMCNT == 0b000001 & VMCNT == 0b0000000 then {
        print("\n[PASS] FLAT Store successful!");
        print_bits("Memory at 0x1008: ", mem_res);
        print("LGKMCNT correctly incremented to 1 for Shared Memory.")
    } else {
        print("\n[FAIL] FLAT Store failed.");
        print_bits("Expected Memory 0xCAFEBABE, Got: ", mem_res);
        print_bits("Expected LGKMCNT 1, Got: ", LGKMCNT)
    };

    print("\n")
}

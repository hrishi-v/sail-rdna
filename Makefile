SAIL_LIB_DIR := ./sail_lib
C_BUILD_DIR  := ./c_build
C_BUILD_OUT  := $(C_BUILD_DIR)/out

SRCS         := $(wildcard spec/*.sail) $(wildcard spec/*/*.sail)
EMU          := rdna3_emu

CXXFLAGS     := -std=c++17 -O2 -I. -I$(C_BUILD_DIR) -I$(SAIL_LIB_DIR) -I./test_harness
OBJ_FILES    := main.o FlightRecorder.o utils.o out.o sail.o rts.o elf.o

ASM_DIR      := tests/asm
ELF_DIR      := tests/elf
BIN_DIR      := tests/bin
ASM_SRCS     := $(wildcard $(ASM_DIR)/*.asm)
ASM_ELFS     := $(patsubst $(ASM_DIR)/%.asm, $(ELF_DIR)/%.elf, $(ASM_SRCS))
RAW_BINS     := $(patsubst $(ASM_DIR)/%.asm, $(BIN_DIR)/%.bin, $(ASM_SRCS))

OBJCOPY      := llvm-objcopy
AS           := clang
ASFLAGS      := -target amdgcn-amd-amdhsa -mcpu=gfx1100 -c

type:
	sail spec/rdna3_main.sail

emu: $(SRCS) test_harness/main.cpp test_harness/utils.cpp
	mkdir -p $(C_BUILD_DIR)
	sail -c -c_no_main spec/rdna3_main.sail -o $(C_BUILD_OUT)
	g++ $(CXXFLAGS) -c test_harness/main.cpp -o main.o
	g++ $(CXXFLAGS) -c test_harness/FlightRecorder.cpp -o FlightRecorder.o
	g++ $(CXXFLAGS) -c test_harness/utils.cpp -o utils.o
	gcc -c -O2 $(C_BUILD_OUT).c -I$(SAIL_LIB_DIR) -o out.o
	gcc -c -O2 $(SAIL_LIB_DIR)/sail.c -I$(SAIL_LIB_DIR) -o sail.o
	gcc -c -O2 $(SAIL_LIB_DIR)/rts.c -I$(SAIL_LIB_DIR) -o rts.o
	gcc -c -O2 $(SAIL_LIB_DIR)/elf.c -I$(SAIL_LIB_DIR) -o elf.o
	g++ -O2 $(OBJ_FILES) -lgmp -lz -o $(EMU)
	rm -f *.o

test: emu assemble
	@./$(EMU)

assemble: $(ASM_ELFS) $(RAW_BINS)

$(ELF_DIR)/%.elf: $(ASM_DIR)/%.asm | $(ELF_DIR)
	$(AS) $(ASFLAGS) $< -o $@

$(BIN_DIR)/%.bin: $(ELF_DIR)/%.elf | $(BIN_DIR)
	$(OBJCOPY) -O binary -j .text $< $@

$(ELF_DIR) $(BIN_DIR):
	mkdir -p $@

fmt:
	@for file in $(SRCS); do \
		sail -fmt "$$file"; \
	done

clean:
	rm -rf $(C_BUILD_DIR) test_output.log $(EMU) *.o $(BIN_DIR) $(ELF_DIR)
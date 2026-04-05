SAIL_LIB_DIR := ./sail_lib
C_BUILD_DIR  := ./build/sail
C_BUILD_OUT  := $(C_BUILD_DIR)/out
OBJ_DIR      := $(C_BUILD_DIR)/obj
EMU          := rdna3_emu

SRCS         := $(wildcard spec/*.sail) $(wildcard spec/*/*.sail)

CXXFLAGS     := -std=c++17 -O2 -MMD -MP -I. -I$(C_BUILD_DIR) -I$(SAIL_LIB_DIR) -I./test_harness/include
CFLAGS       := -O2 -MMD -MP -I$(SAIL_LIB_DIR)
LDFLAGS      := -lgmp -lz

OBJ_FILES    := $(OBJ_DIR)/main.o $(OBJ_DIR)/FlightRecorder.o $(OBJ_DIR)/utils.o \
                $(OBJ_DIR)/out.o $(OBJ_DIR)/sail.o $(OBJ_DIR)/rts.o $(OBJ_DIR)/elf.o

ASM_DIR      := tests/asm
ELF_DIR      := tests/elf
BIN_DIR      := tests/bin
ASM_SRCS     := $(wildcard $(ASM_DIR)/*.asm)
ASM_ELFS     := $(patsubst $(ASM_DIR)/%.asm, $(ELF_DIR)/%.elf, $(ASM_SRCS))
RAW_BINS     := $(patsubst $(ASM_DIR)/%.asm, $(BIN_DIR)/%.bin, $(ASM_SRCS))

OBJCOPY      := $(shell which llvm-objcopy 2>/dev/null || which objcopy)
AS           := clang
ASFLAGS      := -target amdgcn-amd-amdhsa -mcpu=gfx1100 -c

.PHONY: all type emu test assemble fmt clean

all: emu assemble

type:
	sail spec/rdna3_main.sail

emu: $(EMU)

$(EMU): $(OBJ_FILES)
	g++ -O2 $^ $(LDFLAGS) -o $@

$(C_BUILD_OUT).c: $(SRCS) | $(C_BUILD_DIR)
	sail -c -c_no_main spec/rdna3_main.sail -o $(C_BUILD_OUT)

$(OBJ_DIR)/main.o: test_harness/main.cpp | $(OBJ_DIR)
	g++ $(CXXFLAGS) -c $< -o $@

$(OBJ_DIR)/%.o: test_harness/src/%.cpp | $(OBJ_DIR)
	g++ $(CXXFLAGS) -c $< -o $@

$(OBJ_DIR)/out.o: $(C_BUILD_OUT).c | $(OBJ_DIR)
	gcc $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/%.o: $(SAIL_LIB_DIR)/%.c | $(OBJ_DIR)
	gcc $(CFLAGS) -c $< -o $@

test: emu assemble
	@echo "Running Emulator..."
	@./$(EMU)

assemble: $(ASM_ELFS) $(RAW_BINS)

$(ELF_DIR)/%.elf: $(ASM_DIR)/%.asm | $(ELF_DIR)
	$(AS) $(ASFLAGS) $< -o $@

$(BIN_DIR)/%.bin: $(ELF_DIR)/%.elf | $(BIN_DIR)
	$(OBJCOPY) -O binary -j .text $< $@

$(C_BUILD_DIR) $(OBJ_DIR) $(ELF_DIR) $(BIN_DIR):
	mkdir -p $@

fmt:
	@for file in $(SRCS); do \
		sail -fmt "$$file"; \
	done

clean:
	rm -rf build/ test_output.log $(EMU) $(BIN_DIR) $(ELF_DIR)

-include $(OBJ_FILES:.o=.d)
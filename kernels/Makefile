HIPCC        ?= hipcc
HIPFLAGS     := -O1 -g
AS           := clang
ASFLAGS      := -target amdgcn-amd-amdhsa -mcpu=gfx1100 -c
OBJCOPY      := $(shell which llvm-objcopy 2>/dev/null || which objcopy)
STRIP_SCRIPT := ../scripts/strip_asm.py

BUILD        := build
ASM_OUT      := asm
STRIPPED     := stripped
OUT          := outputs
SRCS         := $(wildcard *.hip)
BINS         := $(patsubst %.hip, $(BUILD)/%, $(SRCS))
ASMS         := $(patsubst %.hip, $(ASM_OUT)/%.s, $(SRCS))
STRIPPED_ASMS := $(patsubst %.hip, $(STRIPPED)/%.asm, $(SRCS))
STRIPPED_ELFS := $(patsubst %.hip, $(STRIPPED)/%.elf, $(SRCS))
STRIPPED_BINS := $(patsubst %.hip, $(STRIPPED)/%.bin, $(SRCS))

.PHONY: all run dump-asm strip-asm assemble-stripped clean

all: $(BINS)

$(BUILD)/%: %.hip | $(BUILD)
	$(HIPCC) $(HIPFLAGS) $< -o $@

$(ASM_OUT)/%.s: %.hip | $(ASM_OUT)
	$(HIPCC) -O1 -S $< -o $@

$(STRIPPED)/%.asm: $(ASM_OUT)/%.s | $(STRIPPED)
	python3 $(STRIP_SCRIPT) $< $@

$(STRIPPED)/%.elf: $(STRIPPED)/%.asm | $(STRIPPED)
	$(AS) $(ASFLAGS) $< -o $@

$(STRIPPED)/%.bin: $(STRIPPED)/%.elf
	$(OBJCOPY) -O binary -j .text $< $@

dump-asm: $(ASMS)

strip-asm: $(STRIPPED_ASMS)

assemble-stripped: $(STRIPPED_BINS)

run: all | $(OUT)
	@for bin in $(BINS); do \
		echo "=== Running $$bin ==="; \
		$$bin; \
	done

$(BUILD) $(ASM_OUT) $(STRIPPED) $(OUT):
	mkdir -p $@

clean:
	rm -rf $(BUILD) $(ASM_OUT) $(STRIPPED) $(OUT)

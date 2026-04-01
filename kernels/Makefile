HIPCC    ?= hipcc
HIPFLAGS := -O1 -g

BUILD    := build
ASM_OUT  := asm
SRCS     := $(wildcard *.hip)
BINS     := $(patsubst %.hip, $(BUILD)/%, $(SRCS))
ASMS     := $(patsubst %.hip, $(ASM_OUT)/%.s, $(SRCS))

.PHONY: all run dump-asm clean

all: $(BINS)

$(BUILD)/%: %.hip | $(BUILD)
	$(HIPCC) $(HIPFLAGS) $< -o $@

$(ASM_OUT)/%.s: %.hip | $(ASM_OUT)
	$(HIPCC) -O1 -S $< -o $@

dump-asm: $(ASMS)

run: all
	@for bin in $(BINS); do \
		echo "=== Running $$bin ==="; \
		$$bin; \
	done

$(BUILD) $(ASM_OUT):
	mkdir -p $@

clean:
	rm -rf $(BUILD) $(ASM_OUT)

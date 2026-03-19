HIPCC      := hipcc
HIPFLAGS   := -O0 -g
BUILD_DIR  := build
ASM_DIR    := asm
HARNESS    := harness
SRC        := $(HARNESS)/harness.cpp $(HARNESS)/kernel.hip

TESTS := $(basename $(notdir $(wildcard $(ASM_DIR)/*.inc)))

all: $(TESTS)

$(TESTS):
	@mkdir -p $(BUILD_DIR)
	$(HIPCC) $(HIPFLAGS) \
	  -DTEST_INC=\"../$(ASM_DIR)/$@.inc\" \
	  $(SRC) \
	  -o $(BUILD_DIR)/$@

run: all
	@for t in $(TESTS); do \
	  echo "=== Running $$t ==="; \
	  ./$(BUILD_DIR)/$$t; \
	done

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all run clean $(TESTS)

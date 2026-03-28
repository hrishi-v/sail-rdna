HIPCC ?= hipcc
HIPFLAGS := -O0 -g
BUILD := build
OUT := outputs

add_one_TEST_INC  := ../asm/add_one.inc
add_one_DUMP_INC  := ../asm/add_one_dump.inc
add_one_NUM_VGPRS := 1
add_one_NUM_SGPRS := 0
add_one_VGPR_IDX  := {5}
add_one_SGPR_IDX  := {}

TESTS := add_one

.PHONY: all clean run $(TESTS)

all: $(TESTS)

$(BUILD):
	mkdir -p $(BUILD)

define BUILD_TEST
$(1): $(BUILD)
	$$(HIPCC) $$(HIPFLAGS) \
	  -DTEST_INC='"$$($(1)_TEST_INC)"' \
	  -DDUMP_INC='"$$($(1)_DUMP_INC)"' \
	  -DNUM_VGPRS=$$($(1)_NUM_VGPRS) \
	  -DNUM_SGPRS=$$($(1)_NUM_SGPRS) \
	  -DVGPR_INDICES='$$($(1)_VGPR_IDX)' \
	  -DSGPR_INDICES='$$($(1)_SGPR_IDX)' \
	  -DTEST_NAME='"$(1)"' \
	  harness/harness.cpp harness/kernel.hip \
	  -o $(BUILD)/$(1)
endef

$(foreach t,$(TESTS),$(eval $(call BUILD_TEST,$(t))))

run: all
	@for t in $(TESTS); do \
	  echo "=== Running $$t ==="; \
	  $(BUILD)/$$t; \
	done

clean:
	rm -rf $(BUILD) $(OUT)
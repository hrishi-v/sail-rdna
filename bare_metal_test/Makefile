HIPCC ?= hipcc
HIPFLAGS := -O0 -g -Iharness/include
BUILD := build
OUT := outputs

add_one_TEST_INC  := asm/add_one.inc
add_one_DUMP_INC  := asm/add_one_dump.inc
add_one_NUM_VGPRS := 1
add_one_NUM_SGPRS := 0
add_one_VGPR_IDX  := {5}
add_one_SGPR_IDX  := {}

TESTS := add_one

.PHONY: all clean run $(TESTS)

all: $(TESTS)

$(BUILD) $(OUT):
	mkdir -p $@

HARNESS_SRCS := harness/src/harness.cpp harness/kernel.hip

define BUILD_TEST
$(1): $(BUILD) $(HARNESS_SRCS) $$($(1)_TEST_INC) $$($(1)_DUMP_INC)
	$$(HIPCC) $$(HIPFLAGS) \
		-DTEST_INC='"../../$$($(1)_TEST_INC)"' \
		-DDUMP_INC='"../../$$($(1)_DUMP_INC)"' \
		-DNUM_VGPRS=$$($(1)_NUM_VGPRS) \
		-DNUM_SGPRS=$$($(1)_NUM_SGPRS) \
		-DVGPR_INDICES='$$($(1)_VGPR_IDX)' \
		-DSGPR_INDICES='$$($(1)_SGPR_IDX)' \
		-DTEST_NAME='"$(1)"' \
		$(HARNESS_SRCS) \
		-o $(BUILD)/$(1)
endef

$(foreach t,$(TESTS),$(eval $(call BUILD_TEST,$(t))))

run: all | $(OUT)
	@for t in $(TESTS); do \
		echo "=== Running $$t on RX 7800XT ==="; \
		$(BUILD)/$$t; \
	done

clean:
	rm -rf $(BUILD) $(OUT)
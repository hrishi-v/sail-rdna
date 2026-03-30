HIPCC ?= hipcc
HIPFLAGS := -O0 -g -Iharness/include
BUILD := build
OUT := outputs

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

add_one_TEST_INC        := asm/add_one.inc
add_one_DUMP_INC        := asm/add_one_dump.inc
add_one_NUM_VGPRS       := 1
add_one_NUM_SGPRS       := 0
add_one_VGPR_IDX        := {5}
add_one_SGPR_IDX        := {}
add_one_CAPTURE_PREFIX  := v

v_add_TEST_INC          := asm/v_add.inc
v_add_DUMP_INC          := asm/v_add_dump.inc
v_add_NUM_VGPRS         := 1
v_add_NUM_SGPRS         := 0
v_add_VGPR_IDX          := {0}
v_add_SGPR_IDX          := {}
v_add_CAPTURE_PREFIX    := v

scalar_alu_TEST_INC     := asm/scalar_alu.inc
scalar_alu_DUMP_INC     := asm/scalar_alu_dump.inc
scalar_alu_NUM_VGPRS    := 1
scalar_alu_NUM_SGPRS    := 0
scalar_alu_VGPR_IDX     := {2}
scalar_alu_SGPR_IDX     := {}
scalar_alu_CAPTURE_PREFIX := s

vector_alu_TEST_INC     := asm/vector_alu.inc
vector_alu_DUMP_INC     := asm/vector_alu_dump.inc
vector_alu_NUM_VGPRS    := 1
vector_alu_NUM_SGPRS    := 0
vector_alu_VGPR_IDX     := {1}
vector_alu_SGPR_IDX     := {}
vector_alu_CAPTURE_PREFIX := v

imm_pc_TEST_INC         := asm/imm_pc.inc
imm_pc_DUMP_INC         := asm/imm_pc_dump.inc
imm_pc_NUM_VGPRS        := 1
imm_pc_NUM_SGPRS        := 0
imm_pc_VGPR_IDX         := {2}
imm_pc_SGPR_IDX         := {}
imm_pc_CAPTURE_PREFIX   := v

flat_store_TEST_INC     := asm/flat_store.inc
flat_store_DUMP_INC     := asm/flat_store_dump.inc
flat_store_NUM_VGPRS    := 1
flat_store_NUM_SGPRS    := 0
flat_store_VGPR_IDX     := {3}
flat_store_SGPR_IDX     := {}
flat_store_CAPTURE_PREFIX := v

s_load_b64_test_TEST_INC    := asm/s_load_b64_test.inc
s_load_b64_test_DUMP_INC    := asm/s_load_b64_test_dump.inc
s_load_b64_test_NUM_VGPRS   := 2
s_load_b64_test_NUM_SGPRS   := 0
s_load_b64_test_VGPR_IDX    := {2, 3}
s_load_b64_test_SGPR_IDX    := {}
s_load_b64_test_CAPTURE_PREFIX := s

TESTS := add_one v_add scalar_alu vector_alu imm_pc flat_store s_load_b64_test

# ---------------------------------------------------------------------------
# Build rules
# ---------------------------------------------------------------------------

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
		-DCAPTURE_PREFIX='"$$($(1)_CAPTURE_PREFIX)"' \
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

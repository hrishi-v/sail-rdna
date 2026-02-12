SAIL_DIR = $(shell sail --dir)
C_BUILD_FILES = c_build/out
SRCS = $(wildcard spec/*.sail)

type:
	sail spec/rdna3_main.sail


c: $(SRCS)
	mkdir -p c_build
	sail -c spec/rdna3_main.sail -o $(C_BUILD_FILES)
	gcc -O2 $(C_BUILD_FILES).c $(SAIL_DIR)/lib/*.c -lgmp -lz -I $(SAIL_DIR)/lib/ -o $(C_BUILD_FILES)

clean:
	rm -rf c_build 
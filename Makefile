SAIL_DIR = $(shell sail --dir)
C_BUILD_FILES = c_build/out
SRCS = $(wildcard spec/*.sail)

type:
	sail spec/rdna3_main.sail


c: $(SRCS)
	mkdir -p c_build
	# Compile Sail to C
	sail -c spec/rdna3_main.sail -o $(C_BUILD_FILES)
	# Compile C to Binary (Added -O2 for speed)
	gcc -O2 $(C_BUILD_FILES).c $(SAIL_DIR)/lib/*.c -lgmp -lz -I $(SAIL_DIR)/lib/ -o $(C_BUILD_FILES)

clean:
	rm -rf c_build 
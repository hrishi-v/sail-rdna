SAIL_DIR = $(shell sail --dir)
C_BUILD_FILES = c_build/out

FILES = $(shell find ./spec -name "*.sail")

type:
	sail $(FILES)

c:
	mkdir -p c_build
	sail -c $(FILES) -o $(C_BUILD_FILES)
	gcc $(C_BUILD_FILES).c $(SAIL_DIR)/lib/*.c -lgmp -lz -I $(SAIL_DIR)/lib/ -o $(C_BUILD_FILES)

clean:
	rm -rf c_build
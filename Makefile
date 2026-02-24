SAIL_DIR = $(shell sail --dir)
SAIL_LIB = $(SAIL_DIR)/lib
C_BUILD_FILES = c_build/out
SRCS = $(wildcard spec/*.sail) $(wildcard spec/*/*.sail)
EMU = rdna3_emu

type:
	sail spec/rdna3_main.sail

emu: $(SRCS) main.cpp
	mkdir -p c_build
	# Compile Sail to C
	sail -c -c_no_main spec/rdna3_main.sail -o $(C_BUILD_FILES)
	
	# Compile the C++ Harness
	g++ -c -O2 main.cpp -I c_build/ -I $(SAIL_LIB) -o main.o
	
	# Compile the generated Sail hardware model
	gcc -c -O2 $(C_BUILD_FILES).c -I $(SAIL_LIB) -o out.o
	
	# Compile the Sail runtime files
	gcc -c -O2 $(SAIL_LIB)/sail.c -I $(SAIL_LIB) -o sail.o
	gcc -c -O2 $(SAIL_LIB)/rts.c -I $(SAIL_LIB) -o rts.o
	gcc -c -O2 $(SAIL_LIB)/elf.c -I $(SAIL_LIB) -o elf.o
	
	# Linker
	g++ -O2 main.o out.o sail.o rts.o elf.o -lgmp -lz -o $(EMU)
	
	# 6. Clean up the object files
	rm -f *.o

test: emu
	@./$(EMU) > test_output.log
	@cat test_output.log
	@if grep -q "\[FAIL\]" test_output.log; then \
		echo "TESTS FAILED! Check the output above."; \
		exit 1; \
	else \
		echo "ALL TESTS PASSED!"; \
	fi

clean:
	rm -rf c_build test_output.log $(EMU) *.o
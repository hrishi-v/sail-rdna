{
  description = "Sail RDNA3 Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlayZ3 = final: prev: {
          z3 = prev.z3.overrideAttrs (old: {
            # Disable tests to fix "Trace/BPT trap: 5" on M1 Macs
            doCheck = false;
          });
        };

        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlayZ3 ];
        };

        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          lxml
          numpy
          pytest
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = with pkgs; [
            stdenv.cc
            gnumake
            ocamlPackages.sail
            git
            which
            # Verilator for SystemVerilog simulation
            verilator
            
            llvmPackages.llvm
            llvmPackages.lld
            llvmPackages.bintools

            cargo
            rustc
            rustfmt
          ];

          buildInputs = with pkgs; [
            z3
            pythonEnv
            zlib
            gmp
            ocaml
            dune_3
            ocamlPackages.ocaml-lsp
            nlohmann_json
          ];

          shellHook = ''
            mkdir -p .nix-bin
            ln -sf $(which cc) .nix-bin/gcc
            ln -sf $(which c++) .nix-bin/g++
            export PATH="$PWD/.nix-bin:$PATH"

            export VERILATOR_ROOT="${pkgs.verilator}/share/verilator"
            
            export NLOHMANN_JSON_INC="${pkgs.nlohmann_json}/include"
            export NIX_CFLAGS_COMPILE="-I${pkgs.gmp.dev}/include -I${pkgs.zlib.dev}/include -I$VERILATOR_ROOT/include -I${pkgs.nlohmann_json}/include $NIX_CFLAGS_COMPILE"
            export NIX_LDFLAGS="-L${pkgs.gmp.out}/lib -L${pkgs.zlib.out}/lib $NIX_LDFLAGS"

            echo "Sail Environment Loaded"
            echo "Sail version:      $(sail --version | head -n 1)"
            echo "Z3 version:        $(z3 --version)"
            echo "Verilator version: $(verilator --version)"
            echo "Compiler:          $(gcc --version | head -n 1)"

            ln -snf "$(sail --dir)/lib" ./sail_lib
            # Also link Verilator headers for easier IDE navigation in your harness
            ln -snf "$VERILATOR_ROOT/include" ./verilator_include
            
            echo "Linked Sail StdLib to ./sail_lib"
            echo "Linked Verilator headers to ./verilator_include"
          '';
        };
      }
    );
}
{
  description = "Sail RDNA3 Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # 1. Define an overlay to patch Z3
        overlayZ3 = final: prev: {
          z3 = prev.z3.overrideAttrs (old: {
            # Disable tests to fix "Trace/BPT trap: 5" on M1 Macs
            doCheck = false;
          });
        };

        # 2. Import pkgs WITH the overlay
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlayZ3 ];
        };

        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          lxml
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          # Tools that run on the host (the compiler, make, etc.)
          nativeBuildInputs = with pkgs; [
            stdenv.cc
            gnumake
            ocamlPackages.sail
            git
            which
            llvmPackages.llvm
            llvmPackages.lld
          ];

          # Libraries and language runtimes
          buildInputs = with pkgs; [
            z3
            pythonEnv
            zlib
            gmp
            ocaml
            dune_3
            ocamlPackages.ocaml-lsp
          ];

          shellHook = ''
            # --- MacOS GCC Workaround ---
            # Create a local bin and symlink the Nix compiler to 'gcc' 
            # to bypass the broken Apple shim in /usr/bin/gcc
            mkdir -p .nix-bin
            ln -sf $(which cc) .nix-bin/gcc
            ln -sf $(which c++) .nix-bin/g++
            export PATH="$PWD/.nix-bin:$PATH"

            # Export include and library paths so the compiler finds GMP and Zlib
            export NIX_CFLAGS_COMPILE="-I${pkgs.gmp.dev}/include -I${pkgs.zlib.dev}/include $NIX_CFLAGS_COMPILE"
            export NIX_LDFLAGS="-L${pkgs.gmp.out}/lib -L${pkgs.zlib.out}/lib $NIX_LDFLAGS"

            # --- Status Output ---
            echo "Sail Environment Loaded (Imperial EIE RDNA3 Config)"
            echo "Sail version: $(sail --version | head -n 1)"
            echo "Z3 version:   $(z3 --version)"
            echo "Compiler:     $(gcc --version | head -n 1)"
            
            # Create local symlink to Sail StdLib
            ln -snf "$(sail --dir)/lib" ./sail_lib
            echo "Linked Sail StdLib to ./sail_lib"
          '';
        };
      }
    );
}
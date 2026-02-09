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
          buildInputs = with pkgs; [
            ocamlPackages.sail
            z3  # This will now use the patched version

            pythonEnv
            
            # C & Make Tooling
            gnumake
            zlib
            gmp
            
            # OCaml tooling
            ocaml
            dune_3
            ocamlPackages.ocaml-lsp

            # QoL
            which
          ];

          shellHook = ''
            echo "Sail Environment Loaded"
            echo "Sail version: $(sail --version)"
            echo "Z3 version:   $(z3 --version)"
            echo "Python:       $(python --version)"
            # Create a local symlink to the standard library for easy reference
            # -s = symlink, -n = treat existing link as file, -f = force overwrite
            ln -snf "$(sail --dir)/lib" ./sail_lib
            echo "Linked Sail StdLib to ./sail_lib"
          '';
        };
      }
    );
}
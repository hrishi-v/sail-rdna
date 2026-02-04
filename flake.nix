{
  description = "Sail RDNA3 Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        
        # Define a Python environment with specific packages
        # 'lxml' is added here as an example (it's faster than built-in xml)
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          lxml 
          # You can add others here later, e.g., numpy, pandas, etc.
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Core Tooling
            ocamlPackages.sail
            z3
            
            # The Custom Python Environment
            pythonEnv
            
            # Helper Tools
            gnumake
            zlib
            gmp
            which
            
            # OCaml tooling
            ocaml
            dune_3
            ocamlPackages.ocaml-lsp
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
import re
import json
import sys
from pathlib import Path

def migrate_makefile(makefile_path):
    out_dir = Path('tests/manifests')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(makefile_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find '{makefile_path}'")
        return

    tests_str = ""
    in_tests = False
    
    for line in lines:
        if line.startswith("TESTS :="):
            in_tests = True
            tests_str += line.split(":=")[1].strip().rstrip('\\') + " "
            if not line.rstrip().endswith('\\'): 
                break
        elif in_tests:
            tests_str += line.strip().rstrip('\\') + " "
            if not line.rstrip().endswith('\\'): 
                break

    tests = [t for t in tests_str.split() if t]
    
    if not tests:
        print(f"Failed to find 'TESTS :=' block in {makefile_path}")
        return
        
    print(f"Found {len(tests)} tests! Generating JSON manifests...")
    content = "".join(lines) 

    for t in tests:
        def get_var(suffix, default=""):
            pattern = rf'{t}_{suffix}\s*:=\s*(.+)'
            m = re.search(pattern, content)
            return m.group(1).strip() if m else default

        def parse_indices(val):
            cleaned = val.replace('{', '').replace('}', '').strip()
            if not cleaned: return []
            return [int(x.strip()) for x in cleaned.split(',')]
            
        manifest = {
            "name": t,
            "capture_prefix": get_var("CAPTURE_PREFIX", "v"),
            "assembly": {
                "core_logic": get_var("TEST_INC"),
                "dump_logic": get_var("DUMP_INC")
            },
            "registers": {
                "vgprs": {
                    "count": int(get_var("NUM_VGPRS", "0")),
                    "indices": parse_indices(get_var("VGPR_IDX"))
                },
                "sgprs": {
                    "count": int(get_var("NUM_SGPRS", "0")),
                    "indices": parse_indices(get_var("SGPR_IDX"))
                }
            }
        }
        
        with open(out_dir / f"{t}.json", 'w') as f:
            json.dump(manifest, f, indent=2)
            
    print(f"Successfully migrated {len(tests)} tests to {out_dir}/")

if __name__ == '__main__':
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'bare_metal_test/Makefile'
    migrate_makefile(target_file)
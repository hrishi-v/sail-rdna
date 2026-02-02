import xml.etree.ElementTree as ET
import sys
import re

def clean_tag(tag):
    # Removes {namespace} if present
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def parse_rdna3_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading XML: {e}")
        sys.exit(1)
    
    ast_lines = []
    seen_instructions = set()
    
    print(f"Scanning {xml_file}...")

    # Iterate over ALL tags to find <Instruction> regardless of nesting
    for elem in root.iter():
        tag = clean_tag(elem.tag)
        
        if tag == "Instruction":
            name = "UNKNOWN"
            
            # Look for the <InstructionName> child
            for child in elem:
                if clean_tag(child.tag) == "InstructionName":
                    name = child.text
                    break
            
            # Safety check
            if name == "UNKNOWN" or name is None:
                continue

            # RDNA3 names often have spaces or bad chars? 
            # Usually they are like V_ADD_F32. Let's ensure they are Sail-safe.
            safe_name = name.strip().replace(" ", "_")
            
            # Avoid duplicates (The XML often defines the same instr for multiple encodings)
            if safe_name in seen_instructions:
                continue
            seen_instructions.add(safe_name)

            # Generate the AST line
            # Default signature: (reg_id, reg_id, reg_id) -> We can refine this later
            ast_lines.append(f"    {safe_name} : (reg_id, reg_id, reg_id)")

    print(f"Found {len(ast_lines)} unique instructions.")
    return ast_lines

def generate_files(ast_lines):
    # Sort for deterministic output
    ast_lines.sort()
    
    output_path = "generated/rdna3_ast.sail"
    try:
        with open(output_path, "w") as f:
            f.write("union ast = {\n")
            f.write(",\n".join(ast_lines))
            f.write("\n}\n")
        print(f"Successfully generated: {output_path}")
    except IOError as e:
        print(f"Could not write to file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/gen_sail.py <path_to_xml>")
        print("Example: python3 scripts/gen_sail.py amdgpu_isa_rdna3.xml")
        sys.exit(1)
        
    lines = parse_rdna3_xml(sys.argv[1])
    if lines:
        generate_files(lines)
    else:
        print("No instructions found. Check the XML tag names.")
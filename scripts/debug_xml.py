import xml.etree.ElementTree as ET
import sys

def debug_tags(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print(f"Root Tag: {root.tag}")
        
        # Print the first 5 children to see their names
        print("\nFirst 5 children of root:")
        for i, child in enumerate(root):
            if i > 5: break
            print(f" - {child.tag}")
            
    except Exception as e:
        print(f"Error parsing XML: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_tags(sys.argv[1])
    else:
        print("Usage: python3 debug_xml.py amdgpu_isa_rdna3.xml")
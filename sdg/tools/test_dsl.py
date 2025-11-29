import os
import sys
from sdg.tools.dsl_parser import parse_file

def test_parser(dsl_file):
    try:
        model = parse_file(dsl_file)
        print(f"Successfully parsed {dsl_file}")
        print(f"Dataset Name: {model.name}")
        if model.features:
            print(f"Features: {len(model.features)}")
            for f in model.features:
                print(f"  - {f.name}: {f.formula}")
        print(f"Target: {model.target.name} (Type: {model.target.type})")
        return True
    except Exception as e:
        print(f"Failed to parse {dsl_file}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_dsl.py <dsl_file>")
        sys.exit(1)
    
    dsl_file = sys.argv[1]
    test_parser(dsl_file)

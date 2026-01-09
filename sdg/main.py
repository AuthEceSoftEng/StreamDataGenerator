import sys
import argparse
from sdg.lang import parse_file

def validate_command(args):
    """Validate a DSL file."""
    try:
        model = parse_file(args.file)
        print(f"Validation successful: {args.file}")
        print(f"Dataset Name: {model.name}")
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

def generate_command(args):
    """Generate Python code from a DSL file."""
    try:
        # Parse DSL
        model = parse_file(args.file)
        
        # Generate code using the centralized generator function
        from sdg.generator.codegenerator import sdg_generate
        sdg_generate(None, model, args.output, overwrite=True, debug=False)
            
        print(f"Generated code from: {args.file}")
        
    except Exception as e:
        print(f"Generation failed: {e}")
        sys.exit(1)

def generate_docs_command(args):
    """Generate markdown documentation from a DSL file."""
    try:
        # Parse DSL
        model = parse_file(args.file)
        
        # Generate documentation using the documentation generator
        from sdg.generator.docgenerator import sdg_generate_docs
        output_path = sdg_generate_docs(None, model, args.output, overwrite=True, debug=False)
            
        print(f"Generated documentation: {output_path}")
        
    except Exception as e:
        print(f"Documentation generation failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="StreamDataGenerator DSL CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a DSL file")
    validate_parser.add_argument("file", help="Path to .sdg file")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate Python code from DSL")
    generate_parser.add_argument("file", help="Path to .sdg file")
    generate_parser.add_argument("-o", "--output", help="Output Python file path")
    
    # Generate docs command
    docs_parser = subparsers.add_parser("generate-docs", help="Generate markdown documentation from DSL")
    docs_parser.add_argument("file", help="Path to .sdg file")
    docs_parser.add_argument("-o", "--output", help="Output markdown file path")

    args = parser.parse_args()
    
    if args.command == "validate":
        validate_command(args)
    elif args.command == "generate":
        generate_command(args)
    elif args.command == "generate-docs":
        generate_docs_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

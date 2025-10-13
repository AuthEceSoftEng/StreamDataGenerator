import sys
import yaml
import argparse
import warnings
from sdg.generator.descriptorvalidation import validate_yaml
from sdg.generator.codegenerator import generate, generate_run
from sdg.generator.documentationgenerator import generate_doc

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Python code for a dataset generator')
    parser.add_argument('--input', required=True, help='Path to input YAML file')
    parser.add_argument('--output', required=True, help='Path to output Python file')
    parser.add_argument('--strict', action='store_true', help='Treat all warnings as errors')
    parser.add_argument('--gendoc', action='store_true', help='Generate documentation as HTML')
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    # Read yaml descriptor
    with open(args.input) as infile:
        yamlinput = yaml.safe_load(infile)["dataset"]

    # Validate yaml descriptor
    if args.strict:
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            validate_yaml(yamlinput)
    else:
        validate_yaml(yamlinput)

    # Generate output code
    code = generate(yamlinput)
    coderun = generate_run(yamlinput)
    with open(args.output, 'w') as outfile:
        outfile.write(code + coderun)

    # Generate also documentation
    if args.gendoc:
        doc = generate_doc(args.output)
        with open(args.output[:-2] + "html", 'w') as outfile:
            outfile.write(code + coderun)

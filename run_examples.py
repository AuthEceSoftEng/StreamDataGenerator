#!/usr/bin/env python3
"""
Script to run all examples from the ./examples directory.
Validates, generates, and executes each example, reporting status and metrics.
"""

import os
import sys
import time
import importlib.util
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sdg.lang import parse_file
from sdg.utils.model_converter import convert_model_to_dict
from sdg.generator.codegenerator import generate


def print_table(headers, rows):
    """Print a simple formatted table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in widths)
    
    print(header_line)
    print(separator)
    
    # Print rows
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def validate_example(sdg_file):
    """Validate a DSL file."""
    try:
        model = parse_file(sdg_file)
        return True, model.name, None
    except Exception as e:
        return False, None, str(e)


def generate_code(sdg_file, output_file):
    """Generate Python code from DSL file."""
    start_time = time.time()
    model = parse_file(sdg_file)
    dataset_dict = convert_model_to_dict(model)
    code = generate(dataset_dict)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    generation_time = time.time() - start_time
    return True, generation_time, None


def run_generator(py_file, num_samples=5):
    """Import and run the generated generator."""
    try:
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("generator", py_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the generator class (should be the only class in the module)
        generator_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and hasattr(obj, '__iter__'):
                generator_class = obj
                break
        
        if not generator_class:
            return False, None, "No generator class found"
        
        # Instantiate with seed (most examples use seed parameter)
        try:
            gen = generator_class(seed=42)
        except TypeError:
            # Try without parameters
            gen = generator_class()
        
        # Generate samples
        samples = []
        for i, (X, y) in enumerate(gen):
            if i >= num_samples:
                break
            samples.append((X, y))
        
        return True, samples, None
    except Exception as e:
        return False, None, str(e)


def main():
    """Run all examples and report results."""
    examples_dir = Path("examples")
    results = []
    
    print("=" * 80)
    print("Running Stream Data Generator Examples")
    print("=" * 80)
    print()
    
    # Find all .sdg files (excluding test files)
    sdg_files = sorted([f for f in examples_dir.glob("*.sdg") if not f.name.startswith("test_")])
    
    if not sdg_files:
        print("❌ No .sdg files found in examples directory")
        return 1
    
    for sdg_file in sdg_files:
        print(f"Processing: {sdg_file.name}")
        print("-" * 80)
        
        result = {
            'file': sdg_file.name,
            'validation': '❌',
            'generation': '❌',
            'execution': '❌',
            'gen_time': 0,
            'samples': 0
        }
        
        # Step 1: Validate
        valid, dataset_name, error = validate_example(sdg_file)
        if valid:
            result['validation'] = '✅'
            result['dataset'] = dataset_name
            print(f"  ✅ Validation: OK ({dataset_name})")
        else:
            result['dataset'] = 'N/A'
            print(f"  ❌ Validation: FAILED - {error}")
            results.append(result)
            print()
            continue
        
        # Step 2: Generate code (output_file should be same as sdg_file with py extension)
        output_file = sdg_file.with_suffix('.py')
        gen_ok, gen_time, error = generate_code(sdg_file, output_file)
        if gen_ok:
            result['generation'] = '✅'
            result['gen_time'] = f"{gen_time:.3f}s"
            print(f"  ✅ Generation: OK ({gen_time:.3f}s)")
        else:
            print(f"  ❌ Generation: FAILED - {error}")
            results.append(result)
            print()
            continue
        
        # Step 3: Execute generator
        exec_ok, samples, error = run_generator(output_file)
        if exec_ok:
            result['execution'] = '✅'
            result['samples'] = len(samples)
            print(f"  ✅ Execution: OK ({len(samples)} samples generated)")
            
            # Show first sample
            if samples:
                X, y = samples[0]
                print(f"  📊 Sample: X={X[:3]}..., y={y}")
        else:
            print(f"  ❌ Execution: FAILED - {error}")
        
        # Cleanup generated file
#        try:
#            os.remove(output_file)
#        except:
#            pass
        
        results.append(result)
        print()
    
    # Summary table
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    
    table_data = [
        [
            r['file'],
            r['dataset'],
            r['validation'],
            r['generation'],
            r['execution'],
            r['gen_time'],
            r['samples']
        ]
        for r in results
    ]
    
    headers = ['File', 'Dataset', 'Valid', 'Gen', 'Exec', 'Time', 'Samples']
    print_table(headers, table_data)
    print()
    
    # Statistics
    total = len(results)
    valid_count = sum(1 for r in results if r['validation'] == '✅')
    gen_count = sum(1 for r in results if r['generation'] == '✅')
    exec_count = sum(1 for r in results if r['execution'] == '✅')
    
    print(f"Total examples: {total}")
    print(f"Validated: {valid_count}/{total} ({valid_count/total*100:.0f}%)")
    print(f"Generated: {gen_count}/{total} ({gen_count/total*100:.0f}%)")
    print(f"Executed: {exec_count}/{total} ({exec_count/total*100:.0f}%)")
    print()
    
    # Return exit code
    if exec_count == total:
        print("✅ All examples passed!")
        return 0
    else:
        print("❌ Some examples failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

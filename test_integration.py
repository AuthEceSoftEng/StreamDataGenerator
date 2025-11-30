#!/usr/bin/env python3
"""
Integration test for Stream Data Generator DSL.
Tests code generation and execution for all examples.
"""

import os
import sys
import importlib.util
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sdg.lang import parse_file
from sdg.utils.model_converter import convert_model_to_dict
from sdg.generator.codegenerator import generate


def test_example(sdg_file):
    """
    Test a single example file.
    
    Args:
        sdg_file: Path to .sdg file
        
    Returns:
        dict: Test results
    """
    result = {
        'file': sdg_file.name,
        'parse': False,
        'generate': False,
        'execute': False,
        'validate': False,
        'error': None
    }
    
    try:
        # Step 1: Parse DSL
        model = parse_file(sdg_file)
        result['parse'] = True
        result['dataset_name'] = model.name
        
        # Step 2: Generate code
        dataset_dict = convert_model_to_dict(model)
        code = generate(dataset_dict)
        result['generate'] = True
        
        # Step 3: Execute generated code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location("test_module", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result['execute'] = True
            
            # Find the generator class
            generator_class = getattr(module, model.name)
            
            # Step 4: Validate dataset generation
            # Get parameters from run config
            params = {}
            if hasattr(model, 'run_config') and model.run_config:
                for arg in model.run_config.arguments:
                    params[arg.name] = arg.value
            
            # Instantiate generator
            if params:
                gen = generator_class(**params)
            else:
                gen = generator_class()
            
            # Generate samples
            samples = []
            for i, (X, y) in enumerate(gen):
                if i >= 10:  # Generate 10 samples
                    break
                samples.append((X, y))
            
            # Validate samples
            assert len(samples) == 10, f"Expected 10 samples, got {len(samples)}"
            
            # Check feature count
            expected_features = len(dataset_dict['features'])
            for X, y in samples:
                assert len(X) == expected_features, \
                    f"Expected {expected_features} features, got {len(X)}"
            
            # Check target type
            target_type = dataset_dict['target']['classtype']
            if target_type == 'Binary':
                for X, y in samples:
                    assert y in [0, 1], f"Binary target should be 0 or 1, got {y}"
            elif target_type in ['Float', 'Scalar']:
                for X, y in samples:
                    assert isinstance(y, (int, float)), \
                        f"Numeric target should be int or float, got {type(y)}"
            elif target_type == 'Integer':
                for X, y in samples:
                    assert isinstance(y, int), f"Integer target should be int, got {type(y)}"
            
            # Test drift functionality if available
            if hasattr(gen, 'data_drift'):
                # Test data drift
                for feature in dataset_dict['features']:
                    if 'drift' in feature:
                        gen.data_drift(feature['name'])
                        # Generate one sample after drift
                        next(iter(gen))
            
            if hasattr(gen, 'concept_drift'):
                # Test concept drift
                if 'drift' in dataset_dict['target']:
                    gen.concept_drift()
                    # Generate one sample after drift
                    next(iter(gen))
            
            result['validate'] = True
            result['samples_generated'] = len(samples)
            result['feature_count'] = expected_features
            result['target_type'] = target_type
            
        finally:
            # Cleanup temp file
            os.unlink(temp_file)
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    """Run tests on all examples."""
    examples_dir = Path("examples")
    
    # Find all .sdg files (excluding test files)
    sdg_files = sorted([f for f in examples_dir.glob("*.sdg") 
                       if not f.name.startswith("test_")])
    
    if not sdg_files:
        print("❌ No .sdg files found in examples directory")
        return 1
    
    print("=" * 80)
    print("Integration Test: Code Generation and Validation")
    print("=" * 80)
    print()
    
    results = []
    for sdg_file in sdg_files:
        print(f"Testing: {sdg_file.name}")
        print("-" * 80)
        
        result = test_example(sdg_file)
        results.append(result)
        
        # Print results
        print(f"  Parse:    {'✅' if result['parse'] else '❌'}")
        print(f"  Generate: {'✅' if result['generate'] else '❌'}")
        print(f"  Execute:  {'✅' if result['execute'] else '❌'}")
        print(f"  Validate: {'✅' if result['validate'] else '❌'}")
        
        if result['validate']:
            print(f"  Dataset:  {result['dataset_name']}")
            print(f"  Samples:  {result['samples_generated']}")
            print(f"  Features: {result['feature_count']}")
            print(f"  Target:   {result['target_type']}")
        
        if result['error']:
            print(f"  Error:    {result['error']}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    
    total = len(results)
    parsed = sum(1 for r in results if r['parse'])
    generated = sum(1 for r in results if r['generate'])
    executed = sum(1 for r in results if r['execute'])
    validated = sum(1 for r in results if r['validate'])
    
    print(f"Total examples:    {total}")
    print(f"Parsed:            {parsed}/{total} ({parsed/total*100:.0f}%)")
    print(f"Generated:         {generated}/{total} ({generated/total*100:.0f}%)")
    print(f"Executed:          {executed}/{total} ({executed/total*100:.0f}%)")
    print(f"Validated:         {validated}/{total} ({validated/total*100:.0f}%)")
    print()
    
    # Failed tests
    failed = [r for r in results if not r['validate']]
    if failed:
        print("Failed tests:")
        for r in failed:
            print(f"  ❌ {r['file']}: {r['error']}")
        print()
        return 1
    else:
        print("✅ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

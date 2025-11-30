#!/usr/bin/env python3
"""
Export datasets to CSV or ARFF format from generated code.
Drift is defined in the DSL model and triggered automatically.
"""

import argparse
import sys
import importlib.util
import pandas as pd
from pathlib import Path
from random import seed


def export_dataset(generator_file, output_file, num_instances=10000, random_seed=42, 
                   num_drifts=0):
    """
    Export a dataset from a generated Python file to CSV or ARFF.
    
    Args:
        generator_file: Path to generated Python file
        output_file: Output file path (.csv or .arff)
        num_instances: Number of instances to generate
        random_seed: Random seed
        num_drifts: Number of times to trigger drift (evenly distributed)
    """
    # Set random seed
    seed(random_seed)
    
    # Load the generator module
    spec = importlib.util.spec_from_file_location("generator_module", generator_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find the generator class
    generator_class = None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and hasattr(obj, '__iter__') and name != 'type':
            generator_class = obj
            break
    
    if not generator_class:
        raise ValueError("No generator class found in file")
    
    # Instantiate generator
    gen = generator_class(seed=random_seed)
    
    print(f"Using data generator: {gen.dataset_name}")
    print(f"Creating a dataset of {num_instances} instances")
    
    # Check what drifts are available from the model
    has_concept_drift = hasattr(gen, 'concept_drift') and hasattr(gen, 'driftable_variables')
    has_data_drift = hasattr(gen, 'data_drift') and hasattr(gen, 'driftable_variables')
    
    # Calculate drift positions if requested
    drift_positions = []
    if num_drifts > 0 and (has_concept_drift or has_data_drift):
        # Distribute drifts evenly throughout the dataset
        interval = num_instances // (num_drifts + 1)
        drift_positions = [interval * (i + 1) for i in range(num_drifts)]
        print(f"  with {num_drifts} drift triggers at positions: {drift_positions}")
        
        if has_concept_drift:
            driftable = [v for v in gen.driftable_variables if v == gen.target_name]
            if driftable:
                print(f"    - Concept drift on target: {gen.target_name}")
        
        if has_data_drift:
            driftable_features = [v for v in gen.driftable_variables if v != gen.target_name]
            if driftable_features:
                print(f"    - Data drift on features: {', '.join(driftable_features)}")
    
    print()
    
    # Generate data
    data = []
    for i, (X, y) in enumerate(gen):
        if i >= num_instances:
            break
        
        # Trigger drift at specified positions (uses drift formulas from DSL model)
        if i in drift_positions:
            print(f"Triggering drift at position: {i}")
            
            # Trigger concept drift if available
            if has_concept_drift and gen.target_name in gen.driftable_variables:
                gen.concept_drift()
            
            # Trigger data drift for all driftable features
            if has_data_drift:
                for feature in gen.driftable_variables:
                    if feature != gen.target_name and feature in gen.feature_names:
                        gen.data_drift(feature)
        
        data.append(X + [y])
    
    print()
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=gen.feature_names + [gen.target_name])
    
    # Infer categorical columns
    for column in df:
        if df[column].dtype not in ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
            if 1.0 * df[column].nunique() / df[column].count() < 0.05:
                df[column] = df[column].astype('category')
    
    # Export to file
    if output_file.endswith('.csv'):
        df.to_csv(output_file, index=False)
        print(f"✅ Exported to CSV: {output_file}")
    elif output_file.endswith('.arff'):
        try:
            import arffutils
            arffutils.pandas_dataframe_to_arff(df, output_file, gen.dataset_name, gen.target_name)
            print(f"✅ Exported to ARFF: {output_file}")
        except ImportError:
            print("❌ Error: arffutils not installed. Install with: pip install arffutils")
            sys.exit(1)
    else:
        print(f"❌ Error: Unsupported file format. Use .csv or .arff")
        sys.exit(1)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Features: {', '.join(gen.feature_names)}")
    print(f"Target: {gen.target_name}")


def main():
    parser = argparse.ArgumentParser(
        description='Export datasets to CSV or ARFF format (drift from DSL model)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export 10000 instances to CSV
  python export_dataset.py agrawal0datagenerator.py -o dataset.csv -n 10000
  
  # Export with 4 drift triggers (uses drift formulas from DSL model)
  python export_dataset.py agrawal0datagenerator.py -o dataset.arff -n 10000 --drifts 4
  
  # Export to ARFF without drift
  python export_dataset.py generator.py -o data.arff -n 5000

Note: Drift formulas are defined in the DSL model, not in this CLI.
      The --drifts parameter only specifies HOW MANY times to trigger drift.
        """
    )
    
    parser.add_argument('generator', help='Path to generated Python file')
    parser.add_argument('-o', '--output', required=True, help='Output file path (.csv or .arff)')
    parser.add_argument('-n', '--num-instances', type=int, default=10000, 
                       help='Number of instances to generate (default: 10000)')
    parser.add_argument('-s', '--seed', type=int, default=42, 
                       help='Random seed (default: 42)')
    parser.add_argument('--drifts', type=int, default=0,
                       help='Number of drift triggers (evenly distributed, uses DSL model drift)')
    
    args = parser.parse_args()
    
    # Export dataset
    try:
        export_dataset(
            args.generator,
            args.output,
            num_instances=args.num_instances,
            random_seed=args.seed,
            num_drifts=args.drifts
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

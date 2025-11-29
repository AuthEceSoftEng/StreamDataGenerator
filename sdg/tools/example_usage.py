#!/usr/bin/env python3
"""
Example script showing how to use the textX DSL parser programmatically.
This demonstrates how to load and inspect a dataset definition.
"""

from sdg.tools.dsl_parser import parse_file

def inspect_dataset(dsl_file):
    """Parse and inspect a dataset DSL file."""
    print(f"Parsing {dsl_file}...")
    print("=" * 60)
    
    # Parse the DSL file
    model = parse_file(dsl_file)
    
    # Display dataset information
    print(f"\n📊 Dataset: {model.name}")
    
    if model.description:
        print(f"\n📝 Description:")
        print(f"   {model.description[:100]}...")
    
    # Display parameters
    if model.parameters:
        print(f"\n⚙️  Parameters:")
        for param in model.parameters:
            print(f"   - {param.name}: {param.description}")
    
    # Display features
    if model.features:
        print(f"\n🔢 Features ({len(model.features)} total):")
        for feature in model.features:
            has_drift = " [DRIFT]" if hasattr(feature, 'drift') and feature.drift else ""
            print(f"   - {feature.name}: {feature.description}{has_drift}")
            print(f"     Formula: {feature.formula}")
            if hasattr(feature, 'drift') and feature.drift:
                print(f"     Drift Type: {feature.drift.type}")
                print(f"     Drift Formulas: {len(feature.drift.formulas)}")
    
    # Display target
    if model.target:
        has_drift = " [DRIFT]" if hasattr(model.target, 'drift') and model.target.drift else ""
        print(f"\n🎯 Target: {model.target.name} (Type: {model.target.type}){has_drift}")
        print(f"   Description: {model.target.description}")
        print(f"   Formula: {model.target.formula}")
        if hasattr(model.target, 'drift') and model.target.drift:
            print(f"   Drift Type: {model.target.drift.type}")
            print(f"   Drift Formulas: {len(model.target.drift.formulas)}")
    
    # Display run configuration
    if model.run_config:
        print(f"\n▶️  Run Configuration:")
        for arg in model.run_config.arguments:
            print(f"   - {arg.name} = {arg.value}")
    
    print("\n" + "=" * 60)
    print("✅ Parsing successful!\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <dsl_file>")
        print("\nExample:")
        print("  python example_usage.py sdg/examples/agrawal0.sdg")
        sys.exit(1)
    
    inspect_dataset(sys.argv[1])

#!/usr/bin/env python3
"""
Example script showing how to use the textX DSL parser programmatically.
This demonstrates how to load and inspect a dataset definition.
"""

from sdg.lang import parse_file

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
            print(f"   - {param.name}: {param.description} (Default: {param.default})")
    
    # Map drifts
    drifts_by_target = {}
    if hasattr(model, 'drifts'):
        for drift in model.drifts:
            if drift.target_name not in drifts_by_target:
                drifts_by_target[drift.target_name] = []
            drifts_by_target[drift.target_name].append(drift)

    # Display features
    if model.features:
        print(f"\n🔢 Features ({len(model.features)} total):")
        for feature in model.features:
            has_drift = " [DRIFT]" if feature.name in drifts_by_target else ""
            print(f"   - {feature.name}: {feature.description}{has_drift}")
            print(f"     Formula: {feature.formula}")
            if feature.name in drifts_by_target:
                print(f"     Drifts: {len(drifts_by_target[feature.name])}")
                for drift in drifts_by_target[feature.name]:
                     print(f"       - {drift.name}: {drift.formula}")
    
    # Display target
    if model.target:
        has_drift = " [DRIFT]" if model.target.name in drifts_by_target else ""
        print(f"\n🎯 Target: {model.target.name} (Type: {model.target.type}){has_drift}")
        print(f"   Description: {model.target.description}")
        print(f"   Formula: {model.target.formula}")
        if model.target.name in drifts_by_target:
            print(f"   Drifts: {len(drifts_by_target[model.target.name])}")
            for drift in drifts_by_target[model.target.name]:
                 print(f"     - {drift.name}: {drift.formula}")
    
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

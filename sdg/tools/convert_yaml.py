"""
Convert YAML dataset descriptors to the textX DSL format.
"""

import yaml
import sys


def convert_yaml_to_dsl(yaml_file):
    """Convert YAML dataset descriptor to DSL format."""
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)['dataset']
    
    lines = []
    lines.append(f"dataset {data['name']}")
    
    # Description
    if 'description' in data:
        desc = data['description'].replace('\n', '\\n').replace('"', '\\"')
        lines.append(f'    description: "{desc}"')
        
    if 'imports' in data:
        imports_str = ', '.join(data['imports'])
        lines.append(f'    imports {imports_str}')
    
    # Parameters
    if 'parameters' in data:
        lines.append("    parameters")
        for param in data['parameters']:
            desc = param['description'].replace('"', '\\"')
            lines.append(f'        {param["name"]}: "{desc}"')
        lines.append("    end")
    
    # Features
    if 'features' in data:
        lines.append("    features")
        for feature in data['features']:
            desc = feature.get('description', feature['name']).replace('"', '\\"')
            formula = feature['formula']
            lines.append(f'        {feature["name"]}: {formula}, "{desc}"')
            
            # Drift
            if 'drift' in feature:
                drift = feature['drift']
                lines.append(f"        drift {drift['type']}")
                for df in drift['formulas']:
                    name_part = f"name: {df['name']} " if 'name' in df else ""
                    value = df['value']
                    lines.append(f"            {name_part}value: {value}")
                lines.append("        end")
        
        lines.append("    end")
    
    # Target
    if 'target' in data:
        target = data['target']
        desc = target.get('description', target['name']).replace('"', '\\"')
        lines.append(f'    target {target["name"]}:{target["classtype"]}')
        lines.append(f'        description: "{desc}"')
        lines.append(f'        formula: {target["formula"]}')
        
        # Drift
        if 'drift' in target:
            drift = target['drift']
            lines.append(f"        drift {drift['type']}")
            for df in drift['formulas']:
                name_part = f"name: {df['name']} " if 'name' in df else ""
                value = df['value']
                lines.append(f"            {name_part}value: {value}")
            lines.append("        end")
        lines.append("    end")
    
    # Run configuration
    if 'run' in data:
        args = []
        for arg in data['run'].get('arguments', []):
            val = arg['value']
            if isinstance(val, str):
                val = f'"{val}"'
            args.append(f'{arg["name"]}={val}')
        lines.append(f'    run {", ".join(args)}')
    
    lines.append("end")
    return '\n'.join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_yaml.py <yaml_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    print(convert_yaml_to_dsl(yaml_file))

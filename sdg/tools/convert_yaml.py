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
    lines.append(f"DATASET {data['name']};")
    
    # Description
    if 'description' in data:
        desc = data['description'].replace('\n', '\\n').replace('"', '\\"')
        lines.append(f'DESC "{desc}";')
    
    # Parameters
    if 'parameters' in data:
        for param in data['parameters']:
            desc = param['description'].replace('"', '\\"')
            # Assuming type and default are available or inferred. 
            # If not in YAML, we might need defaults.
            # YAML format isn't fully specified here, but let's assume it matches the dict structure we use elsewhere.
            # If type/default missing, we might need placeholders or error.
            # For now, let's try to get them or use defaults.
            p_type = param.get('type', 'int') # Default to int if missing
            p_default = param.get('default', 0) # Default to 0 if missing
            lines.append(f'PARAM {param["name"]}:{p_type}, "{desc}", {p_default};')
    
    # Features
    if 'features' in data:
        for feature in data['features']:
            desc = feature.get('description', feature['name']).replace('"', '\\"')
            formula = feature['formula']
            # Type is now required in DSL.
            f_type = feature.get('type', 'float') # Default to float
            lines.append(f'FEATURE {feature["name"]}:{f_type}, "{desc}" WITH {formula};')
            
            # Drift
            if 'drift' in feature:
                drift = feature['drift']
                # Drift syntax: DRIFT name:type ON target_name WITH formula;
                # YAML structure for drift seems to be: drift: {type: ..., formulas: [{name: ..., value: ...}]}
                for df in drift['formulas']:
                    d_name = df.get('name', 'drift')
                    d_formula = df['value']
                    # Drift type (e.g. changeformula) comes from drift['type']? 
                    # The DSL expects DRIFT name:type ...
                    # Let's use drift['type'] as the type.
                    d_type = drift['type']
                    lines.append(f'DRIFT {d_name}:{d_type} ON {feature["name"]} WITH {d_formula};')
        
    # Target
    if 'target' in data:
        target = data['target']
        desc = target.get('description', target['name']).replace('"', '\\"')
        formula = target['formula']
        t_type = target.get('classtype', 'binary') # Default to binary, note lowercase
        lines.append(f'TARGET {target["name"]}:{t_type}, "{desc}" WITH {formula};')
        
        # Drift
        if 'drift' in target:
            drift = target['drift']
            for df in drift['formulas']:
                d_name = df.get('name', 'drift')
                d_formula = df['value']
                d_type = drift['type']
                lines.append(f'DRIFT {d_name}:{d_type} ON {target["name"]} WITH {d_formula};')
    
    return '\n'.join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_yaml.py <yaml_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    print(convert_yaml_to_dsl(yaml_file))

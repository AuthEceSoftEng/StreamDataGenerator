import os
from jinja2 import Environment, FileSystemLoader

def prepare_feature_for_template(feature):
    """Prepare feature dictionary for template."""
    feat_data = {
        "name": feature["name"],
        "description": feature["description"],
        "formula": feature["formula"],
        "type": feature["type"],
        "has_drift": "drift" in feature
    }
    
    if feat_data["has_drift"]:
        drift_funcs = []
        # Function 0 is the base formula
        drift_funcs.append({
            "name": f"_{feature['name']}_function_0",
            "formula": feature["formula"]
        })
        # Subsequent functions from drift formulas
        for i, df in enumerate(feature["drift"]["formulas"]):
            drift_funcs.append({
                "name": f"_{feature['name']}_function_{i+1}",
                "formula": df["value"]
            })
        feat_data["drift_functions"] = drift_funcs
        
    return feat_data

def prepare_target_for_template(target):
    """Prepare target dictionary for template."""
    target_data = {
        "name": target["name"],
        "description": target["description"],
        "classtype": target["classtype"],
        "formula": target["formula"],
        "has_drift": "drift" in target
    }
    
    if target_data["has_drift"]:
        drift_funcs = []
        # Function 0 is the base formula
        drift_funcs.append({
            "name": f"_{target['name']}_function_0",
            "formula": target["formula"]
        })
        # Subsequent functions from drift formulas
        for i, df in enumerate(target["drift"]["formulas"]):
            drift_funcs.append({
                "name": f"_{target['name']}_function_{i+1}",
                "formula": df["value"]
            })
        target_data["drift_functions"] = drift_funcs
        
    return target_data

def generate(dataset_dict):
    """
    Generate Python code using Jinja2 template.
    
    Args:
        dataset_dict: Dictionary representation of the dataset (from model_converter)
    """
    # Prepare data for template
    context = {
        "name": dataset_dict["name"],
        "description": dataset_dict["description"],
        "parameters": dataset_dict["parameters"],
        "features": [prepare_feature_for_template(f) for f in dataset_dict["features"]],
        "target": prepare_target_for_template(dataset_dict["target"]),
        "has_drift": any("drift" in f for f in dataset_dict["features"]) or "drift" in dataset_dict["target"]
    }

    # Load template
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Add custom filter for quoting strings if needed, or just use python logic
    # The template uses `map('string_format', '"%s"')` which implies we need a filter.
    # Let's just add a simple quote filter.
    def quote_list(l):
        return [f'"{x}"' for x in l]
    env.filters['quote_list'] = quote_list
    
    template = env.get_template('generator.py.jinja2')
    
    return template.render(context)

def sdg_generate(metamodel, model, output_path, overwrite, debug, **custom_args):
    """
    Generator function for textX registration.
    """
    # Convert model to dict
    from sdg.utils.model_converter import convert_model_to_dict
    dataset_dict = convert_model_to_dict(model)
    
    # Generate code
    code = generate(dataset_dict)
    
    # Determine output path
    if not output_path:
        output_path = f"{dataset_dict['name'].lower()}.py"
        
    # Write to file
    with open(output_path, 'w') as f:
        f.write(code)

from textx import GeneratorDesc

sdg_gen_desc = GeneratorDesc(
    language='sdg',
    target='sdg_gen',
    description='Generate Python code for Stream Data Generator',
    generator=sdg_generate
)


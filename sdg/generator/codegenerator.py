from textx import GeneratorDesc
import os
from jinja2 import Environment, FileSystemLoader


# def prepare_feature_for_template(feature):
#     """Prepare feature dictionary for template."""
#     feat_data = {
#         "name": feature["name"],
#         "description": feature["description"],
#         "formula": feature["formula"],
#         "type": feature["type"],
#         "has_drift": "drift" in feature
#     }

#     if feat_data["has_drift"]:
#         drift_funcs = []
#         # Function 0 is the base formula
#         drift_funcs.append({
#             "name": f"_{feature['name']}_function_0",
#             "formula": feature["formula"]
#         })
#         # Subsequent functions from drift formulas
#         for i, df in enumerate(feature["drift"]["formulas"]):
#             drift_funcs.append({
#                 "name": f"_{feature['name']}_function_{i+1}",
#                 "formula": df["value"]
#             })
#         feat_data["drift_functions"] = drift_funcs

#     return feat_data


# def prepare_target_for_template(target):
#     """Prepare target dictionary for template."""
#     target_data = {
#         "name": target["name"],
#         "description": target["description"],
#         "classtype": target["classtype"],
#         "formula": target["formula"],
#         "has_drift": "drift" in target
#     }

#     if target_data["has_drift"]:
#         drift_funcs = []
#         # Function 0 is the base formula
#         drift_funcs.append({
#             "name": f"_{target['name']}_function_0",
#             "formula": target["formula"]
#         })
#         # Subsequent functions from drift formulas
#         for i, df in enumerate(target["drift"]["formulas"]):
#             drift_funcs.append({
#                 "name": f"_{target['name']}_function_{i+1}",
#                 "formula": df["value"]
#             })
#         target_data["drift_functions"] = drift_funcs

#     return target_data

def prepare_drifts_for_template(drifts):
    """Group drifts by variable and prepare metadata."""
    drift_map = {}

    for drift in drifts:
        var_name = drift["variable"]
        if var_name not in drift_map:
            drift_map[var_name] = []

        drift_map[var_name].append({
            "type": drift["type"],
            "formula": drift["formula"],
            "trigger_point": drift["trigger_point"] or 0,
            "duration": drift["duration"],
            "interval": drift["interval"],
            "transition_steps": drift["transition_steps"]
        })
        
    # Sorting drifts by trigger point within each variable
    for var_name in drift_map:
        drift_map[var_name].sort(key=lambda d: d["trigger_point"])
        
    # Return list of drift specifications
    drift_specs = []
    for var_name, drifts_list in drift_map.items():
        drift_specs.append({
            "variable": var_name,
            "drifts": drifts_list
        })

    return drift_specs


def generate(dataset_dict):
    """
    Generate Python code using Jinja2 template.

    Args:
        dataset_dict: Dictionary representation of the dataset (from model_converter)
    """
    
    drifts = prepare_drifts_for_template(dataset_dict.get("drifts", []))
    
    # Prepare data for template
    context = {
        "name": dataset_dict["name"],
        "description": dataset_dict["description"],
        "parameters": dataset_dict["parameters"],
        "features": dataset_dict["features"],
        "target": dataset_dict["target"],
        "drifts": drifts,
        "has_drift": bool(drifts),
        
    }

    if "run" in dataset_dict and "arguments" in dataset_dict["run"]:
        context["run_config"] = dataset_dict["run"]
        # Pre-format arguments for run config to avoid complex template logic
        run_args = []
        for arg in dataset_dict["run"]["arguments"]:
            run_args.append(f"{arg['name']}={arg['value']}")
        context["run_args_str"] = ", ".join(run_args)

    # Load template
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))

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


sdg_gen_desc = GeneratorDesc(
    language='sdg',
    target='sdg_gen',
    description='Generate Python code for Stream Data Generator',
    generator=sdg_generate
)

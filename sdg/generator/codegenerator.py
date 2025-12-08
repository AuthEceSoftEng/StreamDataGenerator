from textx import GeneratorDesc
import os
from jinja2 import Environment, FileSystemLoader


def prepare_feature_for_template(feature):
    """Prepare feature dictionary for template."""
    return {
        "name": feature["name"],
        "description": feature["description"],
        "formula": feature["formula"],
        "type": feature["type"]
    }


def prepare_target_for_template(target):
    """Prepare target dictionary for template."""
    return {
        "name": target["name"],
        "description": target["description"],
        "classtype": target["classtype"],
        "formula": target["formula"]
    }

def prepare_drifts_for_template(drifts):
    """Prepare drifts for template with feature, drift_types, and scenarios."""
    drift_specs = []
    has_gradual_or_incremental = False
    has_recurring = False

    for drift in drifts:
        drift_types = drift["drift_types"]
        if "gradual" in drift_types or "incremental" in drift_types:
            has_gradual_or_incremental = True
        if "recurring" in drift_types:
            has_recurring = True
        
        drift_specs.append({
            "variable": drift["variable"],
            "drift_types": drift_types,
            "scenarios": drift["scenarios"]
        })

    return drift_specs, has_gradual_or_incremental, has_recurring


def generate(dataset_dict):
    """
    Generate Python code using Jinja2 template.

    Args:
        dataset_dict: Dictionary representation of the dataset (from model_converter)
    """
    
    drifts, has_gradual_or_incremental, has_recurring = prepare_drifts_for_template(dataset_dict.get("drifts", []))
    
    # Prepare data for template
    context = {
        "name": dataset_dict["name"],
        "description": dataset_dict["description"],
        "parameters": dataset_dict["parameters"],
        "features": dataset_dict["features"],
        "target": dataset_dict["target"],
        "drifts": drifts,
        "has_drift": bool(drifts),
        "has_gradual_or_incremental": has_gradual_or_incremental,
        "has_recurring": has_recurring,
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

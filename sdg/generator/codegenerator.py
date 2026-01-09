from textx import GeneratorDesc
import os
import subprocess
from jinja2 import Environment, FileSystemLoader


def format_with_ruff(code_string):
    """
    Format generated Python code using ruff.
    
    :param code_string: The Python code to format
    :returns: Formatted code string
    """
    try:
        # Format with ruff
        result = subprocess.run(
            ['ruff', 'format', '-'],
            input=code_string.encode('utf-8'),
            capture_output=True,
            check=True,
            timeout=10
        )
        formatted = result.stdout.decode('utf-8')
        
        # Apply auto-fixes with ruff check
        result = subprocess.run(
            ['ruff', 'check', '--fix', '--exit-zero', '-'],
            input=formatted.encode('utf-8'),
            capture_output=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            return result.stdout.decode('utf-8')
        
        return formatted
        
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8') if e.stderr else 'Unknown error'
        print(f"Warning: ruff formatting failed: {stderr}")
        return code_string
    except FileNotFoundError:
        print("Warning: ruff not found. Install with: pip install ruff")
        return code_string
    except subprocess.TimeoutExpired:
        print("Warning: ruff formatting timed out")
        return code_string

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


def generate(dataset_dict, format_code=True):
    """
    Generate Python code using Jinja2 template.

    Args:
        dataset_dict: Dictionary representation of the dataset (from model_converter)
        format_code: Whether to format the generated code with ruff (default: True)
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

    code = template.render(context)
    
    # Format code if requested
    if format_code:
        code = format_with_ruff(code)
    
    return code


def sdg_generate(metamodel, model, output_path, overwrite, debug, **custom_args):
    """
    Generator function for textX registration.
    """
    # Convert model to dict
    from sdg.utils.model_converter import convert_model_to_dict
    dataset_dict = convert_model_to_dict(model)

    # Generate code (formatting enabled by default)
    format_code = custom_args.get('format', True)
    code = generate(dataset_dict, format_code=format_code)

    # Determine output path
    if not output_path:
        output_path = f"{dataset_dict['name'].lower()}.py"
        print(output_path)

    # Write to file
    with open(output_path, 'w') as f:
        f.write(code)


sdg_gen_desc = GeneratorDesc(
    language='sdg',
    target='sdg_gen',
    description='Generate Python code for Stream Data Generator',
    generator=sdg_generate
)

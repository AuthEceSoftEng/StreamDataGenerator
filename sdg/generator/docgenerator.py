"""
Documentation generator for Stream Data Generator DSL.
Generates markdown documentation from DSL models.
"""

from jinja2 import Environment, FileSystemLoader
import os


def generate_documentation(dataset_dict, model=None):
    """
    Generate markdown documentation from a dataset dictionary.
    
    Args:
        dataset_dict: Dictionary representation of the dataset model
        model: Original textX model (optional, for preserving DSL formulas)
        
    Returns:
        str: Markdown documentation
    """
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
    
    # Load template
    template = env.get_template('documentation.md.jinja2')
    
    # If model is provided, extract original formulas
    if model:
        # Extract original formulas from model
        for i, feature in enumerate(dataset_dict.get('features', [])):
            if i < len(model.features):
                feature['original_formula'] = str(model.features[i].formula).strip()
        
        # Extract target formula
        if 'target' in dataset_dict and model.target:
            dataset_dict['target']['original_formula'] = str(model.target.formula).strip()
            
            # Extract drift formulas for target
            if 'drift' in dataset_dict['target'] and hasattr(model.target, 'drift') and model.target.drift:
                for i, df in enumerate(dataset_dict['target']['drift']['formulas']):
                    if i < len(model.target.drift.formulas):
                        df['original_value'] = str(model.target.drift.formulas[i].value).strip()
        
        # Extract drift formulas for features
        for i, feature in enumerate(dataset_dict.get('features', [])):
            if 'drift' in feature and i < len(model.features):
                if hasattr(model.features[i], 'drift') and model.features[i].drift:
                    for j, df in enumerate(feature['drift']['formulas']):
                        if j < len(model.features[i].drift.formulas):
                            df['original_value'] = str(model.features[i].drift.formulas[j].value).strip()
    
    # Prepare context
    context = {
        'name': dataset_dict['name'],
        'description': dataset_dict.get('description', ''),
        'parameters': dataset_dict.get('parameters', []),
        'features': dataset_dict.get('features', []),
        'target': dataset_dict.get('target', {})
    }
    
    # Check for drift
    context['has_drift'] = any('drift' in f for f in context['features']) or 'drift' in context['target']
    
    # Render template
    return template.render(**context)


def sdg_generate_docs(metamodel, model, output_path, overwrite, debug, **custom_args):
    """
    Generator function for documentation generation (textX registration).
    
    Args:
        metamodel: textX metamodel (unused)
        model: Parsed DSL model
        output_path: Output file path
        overwrite: Whether to overwrite existing files
        debug: Debug mode flag
        **custom_args: Additional arguments
    """
    from sdg.utils.model_converter import convert_model_to_dict
    
    # Convert model to dict
    dataset_dict = convert_model_to_dict(model)
    
    # Generate documentation (pass model to preserve original formulas)
    docs = generate_documentation(dataset_dict, model)
    
    # Determine output path
    if not output_path:
        output_path = f"{dataset_dict['name'].lower()}_docs.md"
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(docs)
    
    return output_path


# textX generator registration
try:
    from textx import GeneratorDesc
    
    sdg_docs_gen_desc = GeneratorDesc(
        language='sdg',
        target='sdg_docs',
        description='Generate markdown documentation for Stream Data Generator datasets',
        generator=sdg_generate_docs
    )
except ImportError:
    # textX not available
    sdg_docs_gen_desc = None

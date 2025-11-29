from textx import metamodel_from_file
import os

def get_metamodel():
    """Get the metamodel without complex semantic processors."""
    current_dir = os.path.dirname(__file__)
    grammar_path = os.path.join(current_dir, '../grammar/dataset.tx')
    return metamodel_from_file(grammar_path)

def parse_file(file_path, validate_semantics=True):
    """
    Parse a DSL file with optional semantic validation.
    
    Args:
        file_path: Path to the .sdg file
        validate_semantics: If True, run semantic validation
        
    Returns:
        The parsed model
        
    Raises:
        TextXSyntaxError: If syntax is invalid
        TextXSemanticError: If semantics are invalid
    """
    mm = get_metamodel()
    model = mm.model_from_file(file_path)
    
    if validate_semantics:
        from sdg.tools.semantic_validator import validate_model
        validate_model(model)
    
    return model

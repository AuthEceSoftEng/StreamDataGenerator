import os
from textx import metamodel_from_file, LanguageDesc
from sdg.tools.semantic_validator import validate_model

def get_metamodel(debug=False, **kwargs):
    """
    Return the textX metamodel for the SDG language.
    """
    current_dir = os.path.dirname(__file__)
    grammar_path = os.path.join(current_dir, 'grammar', 'dataset.tx')
    mm = metamodel_from_file(grammar_path, debug=debug)
    
    # Register object processor for validation
    def validate(model):
        validate_model(model)
    
    mm.register_obj_processors({'Dataset': validate})
    return mm

language_desc = LanguageDesc(
    name='sdg',
    pattern='*.sdg',
    description='Stream Data Generator DSL',
    metamodel=get_metamodel
)

def parse_file(file_path, debug=False):
    """
    Parse a DSL file.
    """
    mm = get_metamodel(debug=debug)
    return mm.model_from_file(file_path)

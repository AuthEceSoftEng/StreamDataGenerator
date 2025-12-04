"""
Utility to convert textX models to Python-ready dictionaries.
"""

import regex

def _generate_uniform_float_distribution(rangemin, rangemax):
    return "self._rng.uniform(%s, %s)" % (rangemin, rangemax)

def _generate_uniform_integer_distribution(rangemin, rangemax):
    return "self._rng.randint(%s, %s)" % (rangemin, rangemax)

def _generate_gaussian_distribution(mu, sigma):
    return "self._rng.gauss(mu=%s, sigma=%s)" % (mu, sigma)

def _generate_categorical_random(categories):
    return "self._rng.choice([%s])" % (", ".join(categories))

def convert_formula(formulacode):
    """
    Convert a DSL formula string into a valid Python expression.
    Replaces distribution function calls with self._rng calls.
    """
    # Find function calls with nested parentheses support
    formulamatches = regex.finditer(r'(\w+)(?<rec>\((?:[^()]++|(?&rec))*\))', formulacode)
    
    # Process matches in reverse order to maintain indices
    newformulacode = formulacode
    for amatch in reversed(list(formulamatches)):
        matchspan = amatch.span()
        func_name = amatch.group(1)
        args_str = amatch.group(2)[1:-1]  # strip outer parentheses
        arguments = [arg.strip() for arg in args_str.split(',')]
        
        replacement = None
        if func_name == "UniformCategorical":
            replacement = _generate_categorical_random(arguments)
        elif func_name == "UniformInteger":
            if len(arguments) == 2:
                replacement = _generate_uniform_integer_distribution(arguments[0], arguments[1])
        elif func_name == "UniformFloat":
            if len(arguments) == 2:
                replacement = _generate_uniform_float_distribution(arguments[0], arguments[1])
        elif func_name == "Gaussian":
            if len(arguments) == 2:
                replacement = _generate_gaussian_distribution(arguments[0], arguments[1])
            
        if replacement:
            newformulacode = newformulacode[:matchspan[0]] + replacement + newformulacode[matchspan[1]:]
            
    return newformulacode

def _get_type_string(type_obj):
    """
    Convert textX type object to string representation.
    """
    if type_obj is None:
        return None
        
    if isinstance(type_obj, str):
        return type_obj
        
    return str(type_obj)

def convert_model_to_dict(model):
    """
    Convert a textX Dataset model into a dictionary compatible with the code generator.
    """
    result = {
        "name": model.name,
        "description": model.description if hasattr(model, 'description') else "",
        "parameters": [],
        "features": [],
        "target": {},
        "run": {}  # Run config is removed from grammar but kept in dict for compatibility if needed
    }
    
    # Group drifts by target_name
    drifts_by_target = {}
    if hasattr(model, 'drifts'):
        for drift in model.drifts:
            if drift.target_name not in drifts_by_target:
                drifts_by_target[drift.target_name] = []
            drifts_by_target[drift.target_name].append(drift)

    # Parameters
    if hasattr(model, 'parameters') and model.parameters:
        for param in model.parameters:
            result["parameters"].append({
                "name": param.name,
                "description": param.description,
                "type": _get_type_string(param.type),
                "default": param.default
            })
            
    # Features
    if hasattr(model, 'features') and model.features:
        for feature in model.features:
            feat_dict = {
                "name": feature.name,
                "description": feature.description,
                "formula": convert_formula(feature.formula),
                "type": _get_type_string(feature.type)
            }
            
            # Attach drifts
            if feature.name in drifts_by_target:
                drift_formulas = []
                for drift in drifts_by_target[feature.name]:
                    drift_formulas.append({
                        "name": drift.name,
                        "value": convert_formula(drift.formula)
                    })
                feat_dict["drift"] = {
                    "formulas": drift_formulas
                }
            
            result["features"].append(feat_dict)
            
    # Target
    if hasattr(model, 'target') and model.target:
        target = model.target
        target_dict = {
            "name": target.name,
            "description": target.description,
            "classtype": _get_type_string(target.type),
            "formula": convert_formula(target.formula)
        }
        
        # Attach drifts
        if target.name in drifts_by_target:
            drift_formulas = []
            for drift in drifts_by_target[target.name]:
                drift_formulas.append({
                    "name": drift.name,
                    "value": convert_formula(drift.formula)
                })
            target_dict["drift"] = {
                "formulas": drift_formulas
            }
            
        result["target"] = target_dict
        
    return result

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
    Recursively convert textX type object to string representation.
    """
    if type_obj is None:
        return None
        
    if isinstance(type_obj, str):
        return type_obj
        
    # DictType
    if hasattr(type_obj, 'key_type'):
        k = _get_type_string(type_obj.key_type)
        v = _get_type_string(type_obj.value_type)
        if k and v:
            return f"dict[{k}, {v}]"
        return "dict"
        
    # ListType
    if hasattr(type_obj, 'type'):
        t = _get_type_string(type_obj.type)
        if t:
            return f"list[{t}]"
        return "list"
        
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
        "run": {}
    }
    
    # Parameters
    if hasattr(model, 'parameters') and model.parameters:
        for param in model.parameters:
            result["parameters"].append({
                "name": param.name,
                "description": param.description
            })
            
    # Features
    if hasattr(model, 'features') and model.features:
        for feature in model.features:
            feat_dict = {
                "name": feature.name,
                "description": feature.description,
                "formula": convert_formula(feature.formula),
                "type": _get_type_string(feature.type) if hasattr(feature, 'type') else None
            }
            
            if hasattr(feature, 'drift') and feature.drift:
                drift_formulas = []
                for df in feature.drift.formulas:
                    drift_formulas.append({
                        "name": df.name if hasattr(df, 'name') else None,
                        "value": convert_formula(df.value)
                    })
                feat_dict["drift"] = {
                    "type": feature.drift.type,
                    "formulas": drift_formulas
                }
            
            result["features"].append(feat_dict)
            
    # Target
    if hasattr(model, 'target') and model.target:
        target = model.target
        target_dict = {
            "name": target.name,
            "description": target.description,
            "classtype": target.type,
            "formula": convert_formula(target.formula)
        }
        
        if hasattr(target, 'drift') and target.drift:
            drift_formulas = []
            for df in target.drift.formulas:
                drift_formulas.append({
                    "name": df.name if hasattr(df, 'name') else None,
                    "value": convert_formula(df.value)
                })
            target_dict["drift"] = {
                "type": target.drift.type,
                "formulas": drift_formulas
            }
            
        result["target"] = target_dict
        
    # Run config
    if hasattr(model, 'run_config') and model.run_config:
        args = []
        for arg in model.run_config.arguments:
            args.append({
                "name": arg.name,
                "value": arg.value
            })
        result["run"] = {"arguments": args}
        
    return result

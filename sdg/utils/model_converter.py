"""
Utility to convert textX models to Python-ready dictionaries.
"""

import regex
import codecs


def _generate_uniform_float_distribution(rangemin, rangemax):
    return f"self._rng.uniform({rangemin}, {rangemax})"


def _generate_uniform_integer_distribution(rangemin, rangemax):
    return f"self._rng.randint({rangemin}, {rangemax})"


def _generate_gaussian_distribution(mu, sigma):
    return f"self._rng.gauss(mu={mu}, sigma={sigma})"


def _generate_categorical_random(categories):
    return f"self._rng.choice([{', '.join(categories)}])"


def convert_formula(formulacode):
    """
    Convert a DSL formula string into a valid Python expression.
    Replaces distribution function calls with self._rng calls.
    """
    # Find function calls with nested parentheses support
    formulamatches = regex.finditer(
        r'(\w+)(?<rec>\((?:[^()]++|(?&rec))*\))', formulacode)

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
                replacement = _generate_uniform_integer_distribution(
                    arguments[0], arguments[1])
        elif func_name == "UniformFloat":
            if len(arguments) == 2:
                replacement = _generate_uniform_float_distribution(
                    arguments[0], arguments[1])
        elif func_name == "Gaussian":
            if len(arguments) == 2:
                replacement = _generate_gaussian_distribution(
                    arguments[0], arguments[1])

        if replacement:
            newformulacode = newformulacode[:matchspan[0]] + \
                replacement + newformulacode[matchspan[1]:]

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
     # Decode escape sequences in description
    raw_description = getattr(model, 'description', "")
    description = codecs.decode(raw_description, 'unicode_escape') if raw_description else ""
    
    result = {
        "name": model.name,
        "description": description,
        "parameters": [],
        "features": [],
        "target": {},
        "drifts": [],
        "run": {}
    }

    # Parameters
    for param in getattr(model, 'parameters', []):
        result["parameters"].append({
            "name": param.name,
            "description": codecs.decode(getattr(param, 'description', ""), 'unicode_escape')
        })

    # Features
    for feature in getattr(model, 'features', []):
        feat_dict = {
            "name": feature.name,
            "description": codecs.decode(getattr(feature, 'description', ""), 'unicode_escape'),
            "formula": convert_formula(feature.formula),
            "type": _get_type_string(getattr(feature, 'type', None))
        }
        result["features"].append(feat_dict)

    # Target
    target = getattr(model, 'target', None)
    if target:
        result["target"] = {
            "name": target.name,
            "description": codecs.decode(getattr(target, 'description', ""), 'unicode_escape'),
            "classtype": target.type,
            "formula": convert_formula(target.formula)
        }

    # Drifts
    for drift in getattr(model, 'drifts', []):
        drift_points = getattr(drift, "drift_points", [])
        for point in drift_points:
            drift_dict = {
                "variable": drift.variable,
                "type": point.type,
                "formula": convert_formula(drift.formula),
                "trigger_point": point.trigger,
                "duration": getattr(point, "duration", None),
                "transition_steps": getattr(point, "transition_steps", None)
            }
            result["drifts"].append(drift_dict)

    # Run config
    run_config = getattr(model, 'run_config', None)
    if run_config:
        args = []
        for arg in getattr(run_config, 'arguments', []):
            args.append({
                "name": arg.name,
                "value": arg.value
            })
        result["run"] = {"arguments": args}

    return result

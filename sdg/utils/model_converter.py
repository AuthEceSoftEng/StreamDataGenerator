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


def _decode_escapes(text):
    """Decode escape sequences in strings."""
    if not text:
        return ""
    try:
        return codecs.decode(text, 'unicode_escape')
    except Exception:
        return text


def convert_model_to_dict(model):
    """
    Convert a textX Dataset model into a dictionary compatible with the code generator.
    """
    result = {
        "name": model.name,
        "description": _decode_escapes(getattr(model, 'description', "")),
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
            "description": _decode_escapes(getattr(param, 'description', ""))
        })

    # Features
    for feature in getattr(model, 'features', []):
        default_formula = convert_formula(getattr(feature, 'formula', ""))

        scenarios = {}
        for scenario in getattr(feature, 'scenarios', []):
            scenario_name = getattr(scenario, 'name', "")
            scenario_formula = convert_formula(
                getattr(scenario, 'formula', ""))
            scenarios[scenario_name] = scenario_formula

        result["features"].append({
            "name": feature.name,
            "description": _decode_escapes(getattr(feature, 'description', "")),
            "default_formula": default_formula,
            "scenarios": scenarios,
            "type": _get_type_string(getattr(feature, 'type', None))
        })

    # Target
    target = getattr(model, 'target', None)
    if target:
        default_formula = convert_formula(getattr(target, 'formula', ""))

        scenarios = {}
        for scenario in getattr(target, 'scenarios', []):
            scenario_name = getattr(scenario, 'name', "")
            scenario_code = convert_formula((scenario, 'formula', ""))
            scenarios[scenario_name] = scenario_code
            
            result["target"] = {
                "name": target.name,
                "description": _decode_escapes(getattr(target, 'description', "")),
                "classtype": getattr(target, 'type', ""),
                "formula": default_formula,
                "scenarios": scenarios
            }

    # Build lookup map for named formulas
    variable_formulas = {}
    for feature in result["features"]:
        variable_formulas[feature["name"]] = feature["scenarios"]
    variable_formulas[result["target"]["name"]] = result["target"]["scenarios"]

    # Drifts
    for drift in getattr(model, 'drifts', []):
        drift_variable = getattr(drift, 'variable', "")
        feature_scenarios = variable_formulas.get(drift_variable, {})
        
        for point in getattr(drift, 'drift_points', []):
            trigger = getattr(point, 'trigger', 0)
            drift_type = getattr(point, 'drift_type', 'sudden')
            scenario_name = getattr(point, 'scenario_name', None)
            duration = getattr(point, 'duration', None)
            interval = getattr(point, 'interval', None)
            transition = getattr(point, 'transition_steps', None)
            
            drift_formula = feature_scenarios.get(scenario_name, "")
            
            drift_dict = {
                "variable": drift_variable,
                "type": drift_type,
                "trigger_point": trigger,
                "duration": duration,
                "interval": interval,
                "transition_steps": transition,
                "formula": drift_formula,
                "scenario_name": scenario_name
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

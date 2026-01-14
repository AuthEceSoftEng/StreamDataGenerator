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
    return f"self._rng.gauss({mu}, {sigma})"


def _generate_categorical_random(categories):
    return f"self._rng.choice([{', '.join(categories)}])"


def convert_formula(formulacode, feature_names=None):
    """
    Convert a DSL formula string into a valid Python expression.
    Replaces distribution function calls with self._rng calls.
    Optionally replaces feature names with f['name'] access.
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

    # Replace feature references with dictionary access
    if feature_names:
        for name in feature_names:
            # Match whole word only, not inside quotes
            newformulacode = regex.sub(
                rf'\b{name}\b(?!["\'\]])',
                f"features_dict['{name}']",
                newformulacode
            )

    # Support special built-in variables in formulas (e.g. _instance_count)
    # Map DSL special names to their runtime representation in generated code
    special_mappings = {
        '_instance_count': 'self._instance_count'
    }
    for key, val in special_mappings.items():
        # Replace only whole-word occurrences and avoid replacing inside strings or list accesses
        newformulacode = regex.sub(rf"\b{regex.escape(key)}\b(?![\"'\]])", val, newformulacode)

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


def _format_docstring_text(text, base_indent=4):
    """
    Format multi-line text for Python docstrings.
    First line stays at current position, subsequent lines get proper indentation.
    
    :param text: The text to format
    :param base_indent: Number of spaces for base indentation (default: 4)
    :returns: Formatted text with proper indentation
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    if len(lines) == 1:
        return text
    
    # First line as-is, subsequent lines indented
    formatted_lines = [lines[0]]
    indent = ' ' * base_indent
    
    for line in lines[1:]:
        stripped = line.strip()
        if stripped:
            formatted_lines.append(indent + stripped)
        else:
            formatted_lines.append('')
    
    return '\n'.join(formatted_lines)


def convert_model_to_dict(model):
    """
    Convert a textX Dataset model into a dictionary compatible with the code generator.
    """
    result = {
        "name": model.name,
        "description": _format_docstring_text(_decode_escapes(getattr(model, 'description', "")), base_indent=4),
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

    # Collect feature names first
    feature_names = [f.name for f in getattr(model, 'features', [])]
    target = getattr(model, 'target', None)
    if target:
        feature_names.append(target.name)

    # Features - pass feature_names for reference conversion
    for feature in getattr(model, 'features', []):
        default_formula = convert_formula(getattr(feature, 'formula', ""), feature_names)

        result["features"].append({
            "name": feature.name,
            "type": _get_type_string(getattr(feature, 'type', None)),
            "description": _decode_escapes(getattr(feature, 'description', "")),
            "formula": default_formula,
        })

    # Target
    if target:
        default_formula = convert_formula(getattr(target, 'formula', ""), feature_names)

        result["target"] = {
            "name": target.name,
            "description": _decode_escapes(getattr(target, 'description', "")),
            "classtype": getattr(target, 'type', ""),
            "formula": default_formula,
        }

    # Build lookup map for named formulas
    feature_formulas = {}
    for feature in result["features"]:
        feature_formulas[feature["name"]] = feature["formula"]
    feature_formulas[result["target"]["name"]] = result["target"]["formula"]

    # Drifts - convert scenarios with feature references
    # Group drifts by variable to handle multiple drift blocks for the same variable
    drifts_by_variable = {}
    for drift in getattr(model, 'drifts', []):
        drift_variable = drift.variable
        drift_types = drift.drift_types
        raw_scenarios = getattr(drift, 'scenarios', []) or []
        scenarios = [convert_formula(s, feature_names) for s in raw_scenarios]

        if drift_variable not in drifts_by_variable:
            drifts_by_variable[drift_variable] = {
                "drift_types": set(),
                "scenarios": []
            }
        
        # Add drift types (using set to avoid duplicates)
        drifts_by_variable[drift_variable]["drift_types"].update(drift_types)
        
        # Add scenarios
        drifts_by_variable[drift_variable]["scenarios"].extend(scenarios)

    # Convert to final format
    for variable, data in drifts_by_variable.items():
        # Get scenarios and add default formula at the beginning
        scenarios = data["scenarios"]
        default_formula = feature_formulas.get(variable, "")
        if default_formula and default_formula not in scenarios:
            scenarios.insert(0, default_formula)
        
        drift_dict = {
            "variable": variable,
            "drift_types": list(data["drift_types"]),
            "scenarios": scenarios,
        }
        result["drifts"].append(drift_dict)

    return result

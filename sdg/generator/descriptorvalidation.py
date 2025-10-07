import warnings

def validate_yaml(yamlinput):
    if "name" not in yamlinput:
        raise MissingFieldError("Dataset generator must have a name")
    if "description" not in yamlinput:
        warnings.warn("Dataset generator should have a description", MissingFieldWarning)
    if "features" not in yamlinput or len(yamlinput["features"]) == 0:
        raise NoFeaturesError("Dataset generator must have at least one feature")
    if "parameters" not in yamlinput or len(yamlinput["parameters"]) == 0:
        raise MissingFieldError("Dataset generator must have at least a seed parameter")
    if "seed" not in [param["name"] for param in yamlinput["parameters"]]:
        raise MissingFieldError("Dataset generator must have at least a seed parameter named 'seed'")
    if "formula" not in yamlinput["target"]:
        raise MissingFormulaError("Target variable '" + yamlinput["target"]["name"] + "' must have a formula")
    for feature in yamlinput["features"]:
        if "formula" not in feature:
            raise MissingFormulaError("Feature '" + feature["name"] + "' must have a formula")

class MissingFieldError(Exception):
    pass

class MissingFormulaError(Exception):
    pass

class MissingFieldWarning(Warning):
    pass

class NoFeaturesError(Exception):
    pass

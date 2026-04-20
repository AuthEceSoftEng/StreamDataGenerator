"""
Semantic validator for the StreamDataGenerator DSL.

This module implements the well-formedness constraints defined in the
operational semantics document.
"""

import re
from textx.exceptions import TextXSemanticError


class SemanticValidator:
    """Validates semantic properties of the dataset model."""

    def __init__(self, model):
        self.model = model
        self.errors = []
        # Built-in special variables available in formulas (mapped to runtime)
        self.builtins = {'_instance_count'}

    def validate(self):
        """Run all semantic validation checks."""
        self.check_variable_scoping()
        self.check_drift_consistency()
        self.check_type_consistency()
        self.check_distribution_parameters()

        if self.errors:
            raise TextXSemanticError('\n'.join(self.errors))

        return True

    def _collect_all_formulas(self):
        """Collect all formulas from features and target."""
        formulas = []

        if self.model.features:
            for feature in self.model.features:
                if feature.formula:
                    formulas.append(feature.formula)

        if self.model.target and self.model.target.formula:
            formulas.append(self.model.target.formula)

        if getattr(self.model, 'drifts', None):
            for drift in self.model.drifts:
                # Changed: iterate over scenarios list instead of single formula
                for scenario in getattr(drift, 'scenarios', []):
                    if scenario:
                        formulas.append(scenario)

        return formulas

    def check_variable_scoping(self):
        """Verify that formulas only reference variables in scope."""
        # Build parameter set
        param_names = {
            p.name for p in self.model.parameters} if self.model.parameters else set()

        # Check features - each feature can reference params and previous features
        defined_features = set()
        if self.model.features:
            for feature in self.model.features:
                allowed = param_names | defined_features | self.builtins
                free_vars = self._extract_variables(feature.formula)
                undefined = free_vars - allowed

                if undefined:
                    self.errors.append(
                        f"Feature '{feature.name}': undefined variables {undefined} in formula '{feature.formula}'"
                    )
                defined_features.add(feature.name)

        # Check target - can reference params and all features
        if self.model.target:
            allowed = param_names | defined_features | self.builtins
            free_vars = self._extract_variables(self.model.target.formula)
            undefined = free_vars - allowed

            if undefined:
                self.errors.append(
                    f"Target '{self.model.target.name}': undefined variables {undefined} in formula '{self.model.target.formula}'"
                )

        feature_order = [f.name for f in (self.model.features or [])]
        feature_set = set(feature_order)
        target_name = getattr(self.model.target, 'name', None)

        for drift in getattr(self.model, 'drifts', []):
            var = drift.variable
            allowed = set(param_names)
            if var in feature_set:
                # features before var (inclusive)
                idx = feature_order.index(var)
                allowed |= set(feature_order[:idx+1])
            elif target_name and var == target_name:
                # target drift can reference all features
                allowed |= set(feature_order)

            # Changed: validate each scenario formula instead of single drift.formula
            for scenario in getattr(drift, 'scenarios', []):
                free_vars = self._extract_variables(scenario)
                undefined = free_vars - allowed
                if undefined:
                    self.errors.append(
                        f"Drift on '{var}': undefined variables {undefined} in scenario '{scenario}'"
                    )

    def check_drift_consistency(self):
        """Verify drift configurations are consistent."""
        feature_names = {f.name for f in (self.model.features or [])}
        target_name = getattr(self.model.target, 'name', None)

        for drift in getattr(self.model, 'drifts', []):
            var = getattr(drift, 'variable', None)

            # Variable existence
            if var not in feature_names and var != target_name:
                self.errors.append(
                    f"Drift on '{var}': variable does not exist")
                continue

            # Check that at least one scenario is provided
            scenarios = getattr(drift, 'scenarios', [])
            if not scenarios:
                self.errors.append(
                    f"Drift on '{var}': at least one scenario is required")

            # Validate drift types
            drift_types = getattr(drift, 'drift_types', [])
            valid_types = {'sudden', 'gradual', 'incremental', 'recurring'}
            for dtype in drift_types:
                if dtype not in valid_types:
                    self.errors.append(
                        f"Drift on '{var}': invalid drift type '{dtype}'")

            # NEW: Check incremental drift only applies to numeric features
            if 'incremental' in drift_types:
                feature = next(
                    (f for f in self.model.features if f.name == var), None)
                target = self.model.target if target_name == var else None

                if feature and getattr(feature, 'type', 'numeric') == 'categorical':
                    self.errors.append(
                        f"Drift on '{var}': incremental drift cannot be applied to categorical features")
                if target and getattr(target, 'classtype', 'numeric') == 'Binary':
                    self.errors.append(
                        f"Drift on '{var}': incremental drift cannot be applied to binary targets")

    def check_type_consistency(self):
        """Verify that formula types match declared types."""
        # Map feature types to internal type names
        type_map = {
            'int': 'int',
            'float': 'float',
            'string': 'string',
            'bool': 'bool'
        }

        # Target types mapping
        target_type_map = {
            'Binary': 'bool',
            'Scalar': 'numeric',  # Can be int or float
            'Categorical': 'string'
        }

        # Build scope types
        scope_types = {}

        if self.model.features:
            for feature in self.model.features:
                declared_type = type_map.get(feature.type, 'float')
                inferred_type = self._infer_formula_type(
                    feature.formula, scope_types)

                if inferred_type and not self._is_compatible(declared_type, inferred_type):
                    self.errors.append(
                        f"Feature '{feature.name}': type mismatch. Declared '{declared_type}', but formula '{feature.formula}' returns '{inferred_type}'"
                    )
                scope_types[feature.name] = declared_type

        if self.model.target:
            declared_type = target_type_map.get(
                self.model.target.type, 'numeric')
            inferred_type = self._infer_formula_type(
                self.model.target.formula, scope_types)

            if inferred_type and not self._is_compatible(declared_type, inferred_type):
                self.errors.append(
                    f"Target '{self.model.target.name}': type mismatch. Declared '{self.model.target.type}' (expects '{declared_type}'), but formula '{self.model.target.formula}' returns '{inferred_type}'"
                )

        # Check drifts
        for drift in getattr(self.model, 'drifts', []):
            var = drift.variable
            expected_type = scope_types.get(var)
            if not expected_type and self.model.target and var == self.model.target.name:
                expected_type = target_type_map.get(
                    self.model.target.type, 'numeric')

            if expected_type:
                for scenario in getattr(drift, 'scenarios', []):
                    scn_type = self._infer_formula_type(scenario, scope_types)
                    if scn_type and not self._is_compatible(expected_type, scn_type):
                        self.errors.append(
                            f"Drift on '{var}': scenario type mismatch. Variable is '{expected_type}', but scenario '{scenario}' returns '{scn_type}'"
                        )

    def check_distribution_parameters(self):
        """Validate distribution function parameters in all formulas."""
        # Collect all formulas with their context for error reporting
        formula_contexts = []

        if self.model.features:
            for feature in self.model.features:
                if feature.formula:
                    formula_contexts.append(
                        (feature.formula, f"Feature '{feature.name}'"))

        if self.model.target and self.model.target.formula:
            formula_contexts.append(
                (self.model.target.formula, f"Target '{self.model.target.name}'"))

        for drift in getattr(self.model, 'drifts', []):
            for i, scenario in enumerate(getattr(drift, 'scenarios', [])):
                if scenario:
                    formula_contexts.append(
                        (scenario, f"Drift on '{drift.variable}' scenario {i+1}"))

        # Validate each formula
        for formula, context in formula_contexts:
            self._validate_distribution_calls(formula, context)

    def _validate_distribution_calls(self, formula, context):
        """Extract and validate distribution calls from a formula."""
        # Pattern for UniformFloat(min, max) and UniformInteger(min, max)
        uniform_pattern = r'(UniformFloat|UniformInteger)\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)'
        for match in re.finditer(uniform_pattern, formula):
            func_name = match.group(1)
            try:
                min_val = float(match.group(2))
                max_val = float(match.group(3))
                if min_val > max_val:
                    self.errors.append(
                        f"{context}: {func_name}({match.group(2)}, {match.group(3)}) has min > max"
                    )
            except ValueError:
                pass  # Skip if not literal numbers

        # Pattern for Gaussian(mean, sigma)
        gaussian_pattern = r'Gaussian\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)'
        for match in re.finditer(gaussian_pattern, formula):
            try:
                sigma = float(match.group(2))
                if sigma <= 0:
                    self.errors.append(
                        f"{context}: Gaussian({match.group(1)}, {match.group(2)}) has sigma <= 0"
                    )
            except ValueError:
                pass  # Skip if not literal numbers

        # Pattern for UniformCategorical(...) - check at least one value
        categorical_pattern = r'UniformCategorical\s*\(([^)]*)\)'
        for match in re.finditer(categorical_pattern, formula):
            args = match.group(1).strip()
            if not args:
                self.errors.append(
                    f"{context}: UniformCategorical() requires at least one value"
                )

    def _is_compatible(self, declared, inferred):
        if declared == inferred:
            return True
        if declared == 'numeric' and inferred in ['int', 'float']:
            return True
        if declared == 'float' and inferred == 'int':  # promotion
            return True
        if declared == 'bool' and inferred == 'int':  # 0/1 for booleans
            return True
        if inferred == 'numeric' and declared in ['int', 'float']:
            return True
        return False

    def _infer_formula_type(self, formula, scope_types):
        """
        Infer the return type of a formula.
        Simple heuristic implementation.
        """
        if not formula:
            return None

        stripped = formula.strip()

        # Check for string literals (simple case: only a string)
        if (stripped.startswith('"') and stripped.endswith('"')) or \
           (stripped.startswith("'") and stripped.endswith("'")):
            return 'string'

        # Check for boolean operators/comparisons (on formula without strings)
        formula_no_strings = re.sub(r'"[^"]*"', '', formula)
        formula_no_strings = re.sub(r"'[^']*'", '', formula_no_strings)

        has_bool_op = any(op in formula_no_strings for op in [
                          '>', '<', '==', '!=', '>=', '<=', ' and ', ' or ', 'not '])
        is_ternary = ' if ' in formula_no_strings and ' else ' in formula_no_strings

        if has_bool_op and not is_ternary:
            return 'bool'

        if is_ternary:
            # Basic attempt to get the type of the result branch in "A if COND else B"
            parts = re.split(r'\s+if\s+', stripped, maxsplit=1)
            if parts:
                return self._infer_formula_type(parts[0], scope_types)

        # Check for distribution functions
        if 'UniformFloat' in formula or 'Gaussian' in formula:
            return 'float'
        if 'UniformInteger' in formula:
            return 'int'
        if 'UniformCategorical' in formula:
            return 'string'

        # Extract variables and check their types if it's a simple variable reference
        vars_in_formula = self._extract_variables(formula)
        if len(vars_in_formula) == 1 and stripped in vars_in_formula:
            return scope_types.get(stripped)

        # Check for literals
        if re.match(r'^-?\d+\.\d+$', stripped):
            return 'float'
        if re.match(r'^-?\d+$', stripped):
            return 'int'
        if stripped in ['True', 'False']:
            return 'bool'

        return 'numeric'  # Default fallback for math expressions

    def _extract_variables(self, formula):
        """
        Extract variable names from a formula.
        This is a simple heuristic - matches identifiers that are not:
        - Python keywords
        - Known function names
        - Numeric literals
        - String literals
        """
        if not formula:
            return set()

        # Remove string literals first (both single and double quoted)
        formula_no_strings = re.sub(r'"[^"]*"', '', formula)
        formula_no_strings = re.sub(r"'[^']*'", '', formula_no_strings)

        # Known distribution functions and Python keywords
        excluded = {
            'UniformFloat', 'UniformInteger', 'Gaussian', 'UniformCategorical',
            'if', 'else', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None',
            'math', 'sin', 'cos', 'tan', 'pi', 'e', 'sqrt', 'exp', 'log',
            'datetime', 'timedelta', 'weeks', 'days', 'hours', 'minutes',
            'seconds', 'milliseconds', 'microseconds', 'strftime'
        }

        # Match identifiers (alphanumeric + underscore, starting with letter or underscore)
        identifiers = re.findall(
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula_no_strings)

        # Filter out excluded terms
        variables = {var for var in identifiers if var not in excluded}

        return variables


def validate_model(model):
    """
    Validate a dataset model.

    Args:
        model: The textX model to validate

    Raises:
        TextXSemanticError: If validation fails

    Returns:
        True if validation succeeds
    """
    validator = SemanticValidator(model)
    return validator.validate()

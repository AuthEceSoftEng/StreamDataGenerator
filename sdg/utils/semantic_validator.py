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
        
    def validate(self):
        """Run all semantic validation checks."""
        self.check_variable_scoping()
        self.check_drift_consistency()
        self.check_parameter_usage()
        
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
        param_names = {p.name for p in self.model.parameters} if self.model.parameters else set()
        
        # Check features - each feature can reference params and previous features
        defined_features = set()
        if self.model.features:
            for feature in self.model.features:
                allowed = param_names | defined_features
                free_vars = self._extract_variables(feature.formula)
                undefined = free_vars - allowed
                
                if undefined:
                    self.errors.append(
                        f"Feature '{feature.name}': undefined variables {undefined} in formula '{feature.formula}'"
                    ) 
                defined_features.add(feature.name)
        
        # Check target - can reference params and all features
        if self.model.target:
            allowed = param_names | defined_features
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
                self.errors.append(f"Drift on '{var}': variable does not exist")
                continue
            
            # Check that at least one scenario is provided
            scenarios = getattr(drift, 'scenarios', [])
            if not scenarios:
                self.errors.append(f"Drift on '{var}': at least one scenario is required")
            
            # Validate drift types
            drift_types = getattr(drift, 'drift_types', [])
            valid_types = {'sudden', 'gradual', 'incremental', 'recurring'}
            for dtype in drift_types:
                if dtype not in valid_types:
                    self.errors.append(f"Drift on '{var}': invalid drift type '{dtype}'")
            
            # NEW: Check incremental drift only applies to numeric features
            if 'incremental' in drift_types:
                feature = next((f for f in self.model.features if f.name == var), None)
                target = self.model.target if target_name == var else None
                
                if feature and getattr(feature, 'type', 'numeric') == 'categorical':
                    self.errors.append(f"Drift on '{var}': incremental drift cannot be applied to categorical features")
                if target and getattr(target, 'classtype', 'numeric') == 'Binary':
                    self.errors.append(f"Drift on '{var}': incremental drift cannot be applied to binary targets")

    def check_parameter_usage(self):
        """Verify all defined parameters are used in run config."""
        if not self.model.parameters or not self.model.run_config:
            return
        
        param_names = {p.name for p in self.model.parameters}
        run_args = {arg.name for arg in self.model.run_config.arguments} if self.model.run_config.arguments else set()
        
        missing = param_names - run_args
        if missing:
            # This is a warning, not an error
            print(f"Warning: Parameters {missing} are defined but not provided in run config")
        
        extra = run_args - param_names
        if extra:
            self.errors.append(
                f"Run config contains undefined parameters: {extra}"
            )
    
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
            'math', 'sin', 'cos', 'tan', 'pi', 'e', 'sqrt', 'exp', 'log'
        }
        
        # Match identifiers (alphanumeric + underscore, starting with letter or underscore)
        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula_no_strings)
        
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

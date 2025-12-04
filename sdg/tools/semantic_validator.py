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
        self.check_type_consistency()
        
        if self.errors:
            raise TextXSemanticError('\n'.join(self.errors))
        
        return True
    
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
            
            defined_features.add(self.model.target.name)

        # Check drifts
        if hasattr(self.model, 'drifts') and self.model.drifts:
            for drift in self.model.drifts:
                # Drift formula can reference params and all features (including target if it's a concept drift?)
                # Usually drift formula replaces the original formula, so it should have same scope.
                # If it's on a feature, it can see previous features.
                # If it's on target, it can see all features.
                
                target_name = drift.target_name
                
                # Determine scope based on target_name
                allowed = param_names | set(f.name for f in self.model.features) # Default to all features
                
                # If target is a feature, it should only see features defined before it?
                # This is hard to check without order. But generally assuming all features are available is easier,
                # or strict scoping.
                # Let's assume strict scoping:
                if self.model.features:
                    feature_names = [f.name for f in self.model.features]
                    if target_name in feature_names:
                        idx = feature_names.index(target_name)
                        allowed = param_names | set(feature_names[:idx])
                
                free_vars = self._extract_variables(drift.formula)
                undefined = free_vars - allowed
                
                if undefined:
                    self.errors.append(
                        f"Drift '{drift.name}' on '{target_name}': undefined variables {undefined}"
                    )

    def check_drift_consistency(self):
        """Verify drift configurations are consistent."""
        # Check that drift targets exist
        valid_targets = set()
        if self.model.features:
            valid_targets.update(f.name for f in self.model.features)
        if self.model.target:
            valid_targets.add(self.model.target.name)
            
        if hasattr(self.model, 'drifts') and self.model.drifts:
            for drift in self.model.drifts:
                if drift.target_name not in valid_targets:
                    self.errors.append(
                        f"Drift '{drift.name}' refers to undefined target '{drift.target_name}'"
                    )
    
    def check_type_consistency(self):
        """Verify that formulas match their declared types."""
        # Type mapping for distribution functions
        type_inference = {
            'UniformFloat': 'float',
            'Gaussian': 'float',
            'UniformInteger': 'int',
            'UniformCategorical': 'string',
        }
        
        # Check features
        if self.model.features:
            for feature in self.model.features:
                formula = feature.formula.strip()
                declared_type = feature.type
                
                # Check if formula starts with a known distribution function
                for func_name, inferred_type in type_inference.items():
                    if formula.startswith(func_name):
                        if declared_type != inferred_type:
                            self.errors.append(
                                f"Feature '{feature.name}': type mismatch. "
                                f"Declared as '{declared_type}' but formula '{func_name}(...)' returns '{inferred_type}'"
                            )
                        break
        
        # Check target (targets use 'binary' or 'scalar' types, not 'int'/'float')
        # We can still check if the formula makes sense for the type
        if self.model.target:
            formula = self.model.target.formula.strip()
            target_type = self.model.target.type
            
            # For binary targets, formula should be a boolean expression
            # For scalar targets, formula should be numeric
            # This is harder to validate statically, but we can check for obvious mismatches
            
            # Check if formula uses distribution functions (which would be wrong for target)
            for func_name in type_inference.keys():
                if func_name in formula:
                    self.errors.append(
                        f"Target '{self.model.target.name}': targets should not use distribution functions like '{func_name}'. "
                        f"Use feature variables instead."
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

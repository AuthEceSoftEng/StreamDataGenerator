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
    
    def check_imports(self):
        """Verify imports are valid and used."""
        if not self.model.imports:
            return
        
        # Check for duplicate imports
        import_names = [imp.name for imp in self.model.imports]
        seen = set()
        for name in import_names:
            if name in seen:
                self.errors.append(f"Duplicate import: '{name}'")
            seen.add(name)
        
        # Check if imported modules are used in formulas
        all_formulas = self._collect_all_formulas()
        used_imports = set()
        
        for imp in self.model.imports:
            for formula in all_formulas:
                if imp.name in formula:
                    used_imports.add(imp.name)
                    break
        
        unused = set(import_names) - used_imports
        if unused:
            print(f"Warning: Unused imports: {unused}")
    
    def _collect_all_formulas(self):
        """Collect all formulas from features and target."""
        formulas = []
        
        if self.model.features:
            for feature in self.model.features:
                if feature.formula:
                    formulas.append(feature.formula)
                if hasattr(feature, 'drift') and feature.drift:
                    for df in feature.drift.formulas:
                        if df.value:
                            formulas.append(df.value)
        
        if self.model.target and self.model.target.formula:
            formulas.append(self.model.target.formula)
            if hasattr(self.model.target, 'drift') and self.model.target.drift:
                for df in self.model.target.drift.formulas:
                    if df.value:
                        formulas.append(df.value)
        
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
                
                # Check drift formulas
                if hasattr(feature, 'drift') and feature.drift:
                    for df in feature.drift.formulas:
                        free_vars = self._extract_variables(df.value)
                        undefined = free_vars - allowed
                        if undefined:
                            drift_name = f" '{df.name}'" if hasattr(df, 'name') and df.name else ""
                            self.errors.append(
                                f"Feature '{feature.name}' drift{drift_name}: undefined variables {undefined}"
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
            
            # Check target drift formulas
            if hasattr(self.model.target, 'drift') and self.model.target.drift:
                for df in self.model.target.drift.formulas:
                    free_vars = self._extract_variables(df.value)
                    undefined = free_vars - allowed
                    if undefined:
                        drift_name = f" '{df.name}'" if hasattr(df, 'name') and df.name else ""
                        self.errors.append(
                            f"Target '{self.model.target.name}' drift{drift_name}: undefined variables {undefined}"
                        )
    
    def check_drift_consistency(self):
        """Verify drift configurations are consistent."""
        # Check features with drift
        if self.model.features:
            for feature in self.model.features:
                if hasattr(feature, 'drift') and feature.drift:
                    if not feature.drift.formulas:
                        self.errors.append(
                            f"Feature '{feature.name}' has drift but no drift formulas defined"
                        )
        
        # Check target with drift
        if self.model.target and hasattr(self.model.target, 'drift') and self.model.target.drift:
            if not self.model.target.drift.formulas:
                self.errors.append(
                    f"Target '{self.model.target.name}' has drift but no drift formulas defined"
                )
    
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
        
        # Add imported module names to excluded set
        if self.model.imports:
            excluded.update(imp.name for imp in self.model.imports)
        
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

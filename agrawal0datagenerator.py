import random
import itertools
import math

class Agrawal0DataGenerator:
    """
    Stream generator introduced by Agrawal et al.

 Relevant paper:
 Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).
 An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).
 Available online: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf

    Features:
    - salary: Salary
    - commission: Commission
    - age: Age
    - educationlevel: Education Level
    - car: Car Maker
    - zipcode: Zip Code of the Town
    - housevalue: House Value
    - houseyears: Years House Owned
    - loan: Total Loan Amount

    Target:
    - loanapproval: Loan Approval (classification function 0 of the original paper is used)
    """

    # Default values for drift parameters

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        # Drift configurations by feature/target
        # Each drift has: feature name, allowed drift_types, and scenario formulas
        self._drift_configs = {
            "loanapproval": {
                "drift_types": ["sudden"],
                "scenarios": ["age \u003c 40 or 60 \u003c= age", "(age \u003c 40 and 50000 \u003c= salary and salary \u003c= 100000) or (age \u003c 60 and 75000 \u003c= salary and salary \u003c= 125000) or (25000 \u003c= salary and salary \u003c= 75000),"]
            },
        }

        # Drift runtime state per feature
        self._drift_state = {
            "loanapproval": {
                "active": False,
                "current_scenario_idx": 0,
                "current_drift_type": None,
                "drift_points": [],
            },
        }

        self.dataset_name = "Agrawal0DataGenerator"
        self.feature_names = ["salary", "commission", "age", "educationlevel", "car", "zipcode", "housevalue", "houseyears", "loan"]
        self.target_name = "loanapproval"
    def configure_drift(self, feature_name, drift_points, drift_type=None, scenario_idx=None):
        """
        Configure drift for a feature with drift points and parameters.
        
        :param feature_name: Name of the feature to apply drift to
        :param drift_points: List of instance counts at which drift should trigger
        :param drift_type: Type of drift ('sudden', 'gradual', 'incremental', 'recurring')
                          If None, defaults to 'sudden'
        :param scenario_idx: Index of scenario formula to use (0 = default/original)
                            If None, selects randomly when drift triggers
        """
        if feature_name not in self._drift_configs:
            raise ValueError(f"No drift configuration for feature '{feature_name}'")
        
        config = self._drift_configs[feature_name]
        state = self._drift_state[feature_name]
        
        # Validate and set drift type (default to 'sudden')
        if drift_type is None:
            drift_type = "sudden"
        elif config["drift_types"] and drift_type not in config["drift_types"]:
            raise ValueError(f"Drift type '{drift_type}' not allowed for '{feature_name}'. "
                           f"Allowed types: {config['drift_types']}")
        
        # Validate scenario index
        if scenario_idx is not None:
            if scenario_idx < 0 or scenario_idx >= len(config["scenarios"]):
                raise ValueError(f"Invalid scenario index {scenario_idx} for '{feature_name}'. "
                               f"Available scenarios: 0-{len(config['scenarios'])-1}")
        
        # Set drift points (sort them)
        if isinstance(drift_points, int):
            drift_points = [drift_points]
        state["drift_points"] = sorted(drift_points)
        state["current_drift_type"] = drift_type
        state["scenario_idx_config"] = scenario_idx  # None means random selection

    def reset_drift(self, feature_name):
        """
        Reset a feature to its default formula and clear drift configuration.
        
        :param feature_name: Name of the feature to reset
        """
        if feature_name not in self._drift_state:
            raise ValueError(f"No drift state for feature '{feature_name}'")
        
        state = self._drift_state[feature_name]
        state["active"] = False
        state["current_scenario_idx"] = 0
        state["current_drift_type"] = None
        state["drift_points"] = []

    def _check_and_apply_drifts(self):
        """Check if any drift should trigger based on current instance count."""
        for feature_name, state in self._drift_state.items():
            config = self._drift_configs[feature_name]
            drift_type = state.get("current_drift_type")
            
            # Skip if no drift configured
            if not drift_type or not state["drift_points"]:
                continue
            
            # Check if we hit a drift point
            if self._instance_count not in state["drift_points"]:
                self._handle_ongoing_drift(state)
                continue
            
            # Initialize drift at trigger point
            self._initialize_drift(state, config)
    
    def _initialize_drift(self, state, config):
        """Initialize drift when a drift point is hit."""
        # Select scenario
        scenario_idx = state.get("scenario_idx_config")
        if scenario_idx is None:
            scenario_idx = self._rng.randint(1, len(config["scenarios"]) - 1) if len(config["scenarios"]) > 1 else 0
        
        state["active"] = True
        state["current_scenario_idx"] = scenario_idx
    
    def _handle_ongoing_drift(self, state):
        """Handle state updates for ongoing drifts."""
        if not state["active"]:
            return

    def _get_current_formula(self, feature_name, default_formula):
        """
        Get the current formula for a feature considering drift state.
        Handles gradual/incremental transitions with blending.
        """
        if feature_name not in self._drift_state:
            return default_formula
        
        state = self._drift_state[feature_name]
        config = self._drift_configs[feature_name]
        
        if not state["active"]:
            return default_formula
        
        drift_type = state.get("current_drift_type")
        scenario_idx = state["current_scenario_idx"]
        
        if scenario_idx < 0 or scenario_idx >= len(config["scenarios"]):
            return default_formula
        
        target_formula = config["scenarios"][scenario_idx]
        
        # For sudden and recurring, return target formula directly
        if drift_type in ("sudden", "recurring"):
            return target_formula
        
        # For gradual/incremental, handle transition
        if drift_type in ("gradual", "incremental"):
            progress = state["transition_progress"]
            total_steps = state["transition_steps"]
            
            if progress >= total_steps:
                # Transition complete
                return target_formula
            
            # Increment progress
            state["transition_progress"] += 1
            
            # Calculate blend ratio
            ratio = progress / total_steps
            
            if drift_type == "gradual":
                # Gradual: probabilistic switching based on ratio
                if self._rng.random() < ratio:
                    return target_formula
                else:
                    return default_formula
            else:
                # Incremental: linear interpolation (returned as expression)
                # For incremental, we need to evaluate both and blend
                return f"(1 - {ratio}) * ({default_formula}) + {ratio} * ({target_formula})"
        
        return target_formula

    def get_drift_info(self):
        """
        Get information about available drifts and their current state.
        
        :returns: Dictionary with drift configurations and state per feature
        """
        return {
            feature: {
                "drift_types": config["drift_types"],
                "num_scenarios": len(config["scenarios"]),
                "scenarios": config["scenarios"],
                "current_state": {
                    "active": self._drift_state[feature]["active"],
                    "drift_type": self._drift_state[feature]["current_drift_type"],
                    "scenario_idx": self._drift_state[feature]["current_scenario_idx"],
                    "drift_points": self._drift_state[feature]["drift_points"],
                }
            }
            for feature, config in self._drift_configs.items()
        }

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples (X, y): X is feature list, y is target.
        """
        while True:
            self._check_and_apply_drifts()
            _salary_expr = self._get_current_formula("salary", "self._rng.uniform(20000, 150000)")
            salary = eval(_salary_expr)
            _commission_expr = self._get_current_formula("commission", "0 if salary < 75000 else self._rng.uniform(10000, 75000)")
            commission = eval(_commission_expr)
            _age_expr = self._get_current_formula("age", "self._rng.randint(20, 80)")
            age = eval(_age_expr)
            _educationlevel_expr = self._get_current_formula("educationlevel", "self._rng.randint(0, 4)")
            educationlevel = eval(_educationlevel_expr)
            _car_expr = self._get_current_formula("car", "self._rng.randint(1, 20)")
            car = eval(_car_expr)
            _zipcode_expr = self._get_current_formula("zipcode", "self._rng.randint(0, 8)")
            zipcode = eval(_zipcode_expr)
            _housevalue_expr = self._get_current_formula("housevalue", "self._rng.uniform(50000 * zipcode, 100000 * zipcode)")
            housevalue = eval(_housevalue_expr)
            _houseyears_expr = self._get_current_formula("houseyears", "self._rng.randint(1, 30)")
            houseyears = eval(_houseyears_expr)
            _loan_expr = self._get_current_formula("loan", "self._rng.uniform(0, 500000)")
            loan = eval(_loan_expr)
            _loanapproval_expr = self._get_current_formula("loanapproval", "age < 40 or 60 <= age")
            loanapproval = 1 if eval(_loanapproval_expr) else 0

            self._instance_count += 1
            yield [salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan], loanapproval

    def get_n_instances(self, numinstances):
        """
        Generates and returns the number of data instances that is given as a parameter.
        """
        return itertools.islice(self, numinstances)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Agrawal0DataGenerator - Stream Data Generator')
    parser.add_argument('--seed', type=type(42), default=42, help='The seed of the random generator')
    parser.add_argument('--samples', type=int, default=150, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    # Initialize generator with parsed arguments
    gen = Agrawal0DataGenerator(seed=args.seed)
    
    # Generate and print samples
    for i, (X, y) in enumerate(gen.get_n_instances(args.samples)):
        print(f"Instance {i}: X={X}, y={y}")
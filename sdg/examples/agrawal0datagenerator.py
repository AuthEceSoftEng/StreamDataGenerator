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
                "scenarios": ["age \u003c 40 or 60 \u003c= age", "(age \u003c 40 and 50000 \u003c= salary and salary \u003c= 100000) or (age \u003c 60 and 75000 \u003c= salary and salary \u003c= 125000) or (25000 \u003c= salary and salary \u003c= 75000)"]
            },
        }

        # Drift runtime state per feature (list of drift configs)
        self._drift_state = {
            "loanapproval": [],
        }

        self.dataset_name = "Agrawal0DataGenerator"
        self.feature_names = ["salary", "commission", "age", "educationlevel", "car", "zipcode", "housevalue", "houseyears", "loan"]
        self.target_name = "loanapproval"

    def add_drift(self, feature_name, drift_type=None, scenario_idx=None):
        """
        Apply drift immediately for a feature at the current instance count.
        """
        if feature_name not in self._drift_configs:
            raise ValueError(f"No drift configuration for feature '{feature_name}'")
        config = self._drift_configs[feature_name]

        drift_type = drift_type or "sudden"
        if config["drift_types"] and drift_type not in config["drift_types"]:
            raise ValueError(f"Drift type '{drift_type}' not allowed for '{feature_name}'. Allowed: {config['drift_types']}")
        if scenario_idx is not None and (scenario_idx < 0 or scenario_idx >= len(config["scenarios"])):
            raise ValueError(f"Invalid scenario index {scenario_idx} for '{feature_name}'")

        current_scenario_idx = scenario_idx if scenario_idx is not None else (
            self._rng.randint(1, len(config["scenarios"]) - 1) if len(config["scenarios"]) > 1 else 0
        )

        new_drift = {
            "active": True,
            "drift_point": self._instance_count,
            "current_drift_type": drift_type,
            "scenario_idx_config": scenario_idx,
            "current_scenario_idx": current_scenario_idx,
        }
        self._drift_state[feature_name].append(new_drift)

    def _check_and_apply_drifts(self):
        """Check drift states (kept for recurring drift support if needed)."""
        pass

    def _initialize_drift(self, feature_name, state, config):
        """Initialize drift when a drift point is hit."""
        scenario_idx = state.get("scenario_idx_config")
        if scenario_idx is None:
            scenario_idx = self._rng.randint(1, len(config["scenarios"]) - 1) if len(config["scenarios"]) > 1 else 0

        state["active"] = True
        state["current_scenario_idx"] = scenario_idx
        print(f"[DRIFT] feature='{feature_name}' type='{state.get('current_drift_type')}' "
              f"scenario={scenario_idx} at instance={self._instance_count}")

    def _handle_ongoing_drift(self, state):
        """Handle state updates for ongoing drifts."""
        if not state["active"]:
            return

    def _get_current_formula(self, feature_name, default_formula):
        """
        Get the current formula for a feature considering drift state.
        If multiple drifts are active, the last activated one wins.
        """
        if feature_name not in self._drift_state:
            return default_formula

        # pick the most recently activated active drift (last in list that is active)
        active = None
        for state in reversed(self._drift_state[feature_name]):
            if state.get("active"):
                active = state
                break
        if not active:
            return default_formula

        config = self._drift_configs[feature_name]
        scenario_idx = active["current_scenario_idx"]
        if scenario_idx < 0 or scenario_idx >= len(config["scenarios"]):
            return default_formula

        target_formula = config["scenarios"][scenario_idx]
        dtype = active.get("current_drift_type")

        if dtype in ("sudden", "recurring"):
            return target_formula

        if dtype in ("gradual", "incremental"):
            progress = active["transition_progress"]
            total = active["transition_steps"]
            if progress >= total:
                return target_formula
            active["transition_progress"] += 1
            ratio = progress / total
            if dtype == "gradual":
                return target_formula if self._rng.random() < ratio else default_formula
            return f"(1 - {ratio}) * ({default_formula}) + {ratio} * ({target_formula})"

        return target_formula

    def get_drift_info(self):
        """Return drift configs and state."""
        return {
            feature: {
                "drift_types": config["drift_types"],
                "num_scenarios": len(config["scenarios"]),
                "scenarios": config["scenarios"],
                "active_drifts": [
                    {
                        "active": state.get("active", False),
                        "drift_type": state.get("current_drift_type"),
                        "scenario_idx": state.get("current_scenario_idx"),
                        "drift_point": state.get("drift_point"),
                    }
                    for state in self._drift_state[feature]
                ]
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
            _commission_expr = self._get_current_formula("commission", "0 if salary \u003c 75000 else self._rng.uniform(10000, 75000)")
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
            _loanapproval_expr = self._get_current_formula("loanapproval", "age \u003c 40 or 60 \u003c= age")
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
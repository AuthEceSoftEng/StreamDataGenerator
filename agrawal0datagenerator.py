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
    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        # Drift configurations by variable
        self._drift_configs = {
            "loanapproval": [{"duration": 0, "formula": "(age \u003c 40 and 50000 \u003c= salary and salary \u003c= 100000) or (age \u003c 60 and 75000 \u003c= salary and salary \u003c= 125000) or (25000 \u003c= salary and salary \u003c= 75000)", "transition_steps": 0, "trigger_point": 150, "type": "sudden"}],
        }

        # Drift runtime state per variable
        self._drift_state = {
            "loanapproval": {
                "active_drift_idx": None,
                "transition_progress": 0
            },
        }

        self.dataset_name = "Agrawal0DataGenerator"
        self.feature_names = ["salary", "commission", "age", "educationlevel", "car", "zipcode", "housevalue", "houseyears", "loan"]
        self.target_name = "loanapproval"
    def _check_and_update_drifts(self):
        """Trigger start/end of drifts based on instance counter."""
        for var_name, drifts in self._drift_configs.items():
            state = self._drift_state[var_name]

            # Start drifts when reaching trigger point
            for idx, cfg in enumerate(drifts):
                if self._instance_count == (cfg.get("trigger_point") or 0):
                    state["active_drift_idx"] = idx
                    state["transition_progress"] = 0

            # End recurring drifts after duration
            if state["active_drift_idx"] is not None:
                idx = state["active_drift_idx"]
                cfg = drifts[idx]
                duration = cfg.get("duration")
                trigger = cfg.get("trigger_point") or 0
                if duration is not None and self._instance_count >= trigger + duration:
                    # Recurring ends -> revert to original
                    state["active_drift_idx"] = None
                    state["transition_progress"] = 0

    def _current_formula(self, var_name, original_formula):
        """
        Resolve current formula considering active drift type.
        - sudden: immediately switch to new_formula
        - gradual: switch after transition_steps
        - incremental: same as sudden (custom interpolation left to generator logic if needed)
        - recurring: same as sudden, but ends after duration
        """
        state = self._drift_state.get(var_name)
        if not state or state["active_drift_idx"] is None:
            return original_formula

        cfg = self._drift_configs[var_name][state["active_drift_idx"]]
        drift_type = cfg.get("type")
        new_formula = cfg.get("formula")

        if drift_type in ("sudden", "recurring", "incremental"):
            return new_formula

        if drift_type == "gradual":
            steps = max(1, int(cfg.get("transition_steps") or 1))
            progress = min(state["transition_progress"] / steps, 1.0)
            state["transition_progress"] += 1
            return new_formula if progress >= 1.0 else original_formula

        return original_formula

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples (X, y): X is feature list, y is target.
        """
        while True:
            self._check_and_update_drifts()
            _salary_expr = self._current_formula("salary", "self._rng.uniform(20000, 150000)")
            salary = eval(_salary_expr)
            _commission_expr = self._current_formula("commission", "0 if salary < 75000 else self._rng.uniform(10000, 75000)")
            commission = eval(_commission_expr)
            _age_expr = self._current_formula("age", "self._rng.randint(20, 80)")
            age = eval(_age_expr)
            _educationlevel_expr = self._current_formula("educationlevel", "self._rng.randint(0, 4)")
            educationlevel = eval(_educationlevel_expr)
            _car_expr = self._current_formula("car", "self._rng.randint(1, 20)")
            car = eval(_car_expr)
            _zipcode_expr = self._current_formula("zipcode", "self._rng.randint(0, 8)")
            zipcode = eval(_zipcode_expr)
            _housevalue_expr = self._current_formula("housevalue", "self._rng.uniform(50000 * zipcode, 100000 * zipcode)")
            housevalue = eval(_housevalue_expr)
            _houseyears_expr = self._current_formula("houseyears", "self._rng.randint(1, 30)")
            houseyears = eval(_houseyears_expr)
            _loan_expr = self._current_formula("loan", "self._rng.uniform(0, 500000)")
            loan = eval(_loan_expr)
            _loanapproval_expr = self._current_formula("loanapproval", "age < 40 or 60 <= age")
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
    parser.add_argument('--samples', type=int, default=5, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    # Initialize generator with parsed arguments
    gen = Agrawal0DataGenerator(seed=args.seed)
    
    # Generate and print samples
    for i, (X, y) in enumerate(gen):
        print(f"Instance {i}: X={X}, y={y}")
        if i >= args.samples - 1:
            break
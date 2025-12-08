import random
import itertools
import math

class StaggerDataGenerator:
    """
    Stream generator producing three boolean features describing objects:
 size, shape and colour. Dataset originally introduced in:
 Schlimmer, J. C., & Granger, R. H. (1986). Incremental learning from.
 noisy data. Machine learning, 1(3), 317-354.

    Features:
    - size: The size of the object, one of small, medium, large
    - shape: The shape of the object, one of circle, square, triangle
    - color: The color of the object, one of red, blue, green

    Target:
    - y: The target variable defined as a function of the features
    """

    # Default values for drift parameters
    DEFAULT_TRANSITION_STEPS = 100

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
            "y": {
                "drift_types": ["sudden", "gradual"],
                "scenarios": ["size == \"small\" and color == \"red\"", "color == \"green\" or shape == \"circle\"", "size == \"medium\" or size == \"large\""]
            },
        }

        # Drift runtime state per feature (list of drift configs)
        self._drift_state = {
            "y": [],
        }

        self.dataset_name = "StaggerDataGenerator"
        self.feature_names = ["size", "shape", "color"]
        self.target_name = "y"

    def add_drift(self, feature_name, drift_points, drift_type=None, scenario_idx=None,
                        transition_steps=None):
        """
        Configure drifts for a feature with drift points and parameters.
        Multiple drift types/points can be provided in one call (parallel arrays).
        """
        if feature_name not in self._drift_configs:
            raise ValueError(f"No drift configuration for feature '{feature_name}'")
        config = self._drift_configs[feature_name]

        # Normalize points
        if isinstance(drift_points, int):
            drift_points = [drift_points]
        num_points = len(drift_points)

        # Normalize drift_type
        if drift_type is None:
            drift_types = ["sudden"] * num_points
        elif isinstance(drift_type, str):
            drift_types = [drift_type] * num_points
        elif isinstance(drift_type, list):
            if len(drift_type) != num_points:
                raise ValueError(f"drift_type list length ({len(drift_type)}) must match drift_points ({num_points})")
            drift_types = drift_type
        else:
            raise TypeError("drift_type must be string or list")

        # Normalize scenario_idx
        if scenario_idx is None:
            scenario_indices = [None] * num_points
        elif isinstance(scenario_idx, int):
            scenario_indices = [scenario_idx] * num_points
        elif isinstance(scenario_idx, list):
            if len(scenario_idx) != num_points:
                raise ValueError(f"scenario_idx list length ({len(scenario_idx)}) must match drift_points ({num_points})")
            scenario_indices = scenario_idx
        else:
            raise TypeError("scenario_idx must be int, list, or None")

        for i, (point, dtype, sidx) in enumerate(zip(drift_points, drift_types, scenario_indices)):
            if config["drift_types"] and dtype not in config["drift_types"]:
                raise ValueError(f"Drift type '{dtype}' not allowed for '{feature_name}'. Allowed: {config['drift_types']}")
            if sidx is not None and (sidx < 0 or sidx >= len(config["scenarios"])):
                raise ValueError(f"Invalid scenario index {sidx} at position {i} for '{feature_name}'")

            new_drift = {
                "active": False,
                "drift_point": point,
                "current_drift_type": dtype,
                "scenario_idx_config": sidx,
                "current_scenario_idx": 0,
                "transition_steps": max(1, transition_steps) if transition_steps else self.DEFAULT_TRANSITION_STEPS,
                "transition_progress": 0,
            }
            self._drift_state[feature_name].append(new_drift)

        # Keep drifts ordered by point
        self._drift_state[feature_name].sort(key=lambda x: x["drift_point"])

    def _check_and_apply_drifts(self):
        """Check if any drift should trigger based on current instance count."""
        for feature_name, drift_list in self._drift_state.items():
            config = self._drift_configs[feature_name]
            for state in drift_list:
                dtype = state.get("current_drift_type")
                if not dtype:
                    continue
                if self._instance_count == state.get("drift_point"):
                    self._initialize_drift(feature_name, state, config)
                else:
                    self._handle_ongoing_drift(state)

    def _initialize_drift(self, feature_name, state, config):
        """Initialize drift when a drift point is hit."""
        scenario_idx = state.get("scenario_idx_config")
        if scenario_idx is None:
            scenario_idx = self._rng.randint(1, len(config["scenarios"]) - 1) if len(config["scenarios"]) > 1 else 0

        state["active"] = True
        state["current_scenario_idx"] = scenario_idx
        print(f"[DRIFT] feature='{feature_name}' type='{state.get('current_drift_type')}' "
              f"scenario={scenario_idx} at instance={self._instance_count}")
        if state.get("current_drift_type") in ("gradual", "incremental"):
            state["transition_progress"] = 0

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
                        "transition_steps": state.get("transition_steps"),
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
            _size_expr = self._get_current_formula("size", "self._rng.choice([\"small\", \"medium\", \"large\"])")
            size = eval(_size_expr)
            _shape_expr = self._get_current_formula("shape", "self._rng.choice([\"circle\", \"square\", \"triangle\"])")
            shape = eval(_shape_expr)
            _color_expr = self._get_current_formula("color", "self._rng.choice([\"red\", \"blue\", \"green\"])")
            color = eval(_color_expr)
            _y_expr = self._get_current_formula("y", "size == \"small\" and color == \"red\"")
            y = 1 if eval(_y_expr) else 0

            self._instance_count += 1
            yield [size, shape, color], y

    def get_n_instances(self, numinstances):
        """
        Generates and returns the number of data instances that is given as a parameter.
        """
        return itertools.islice(self, numinstances)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='StaggerDataGenerator - Stream Data Generator')
    parser.add_argument('--seed', type=type(42), default=42, help='The seed of the random generator')
    parser.add_argument('--samples', type=int, default=150, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    # Initialize generator with parsed arguments
    gen = StaggerDataGenerator(seed=args.seed)
    
    # Generate and print samples
    for i, (X, y) in enumerate(gen.get_n_instances(args.samples)):
        print(f"Instance {i}: X={X}, y={y}")
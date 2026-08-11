import random
import itertools
import math
import datetime


class DriftTypesDemo:
    """
    DriftTypesDemo stream generator.

    Demonstration of gradual, incremental, and recurring drift types within a single stream definition.

    Gradual drift on sensor_a: the distribution switches probabilistically from N(50,5) to N(70,5) over a configurable number of instances.
    Incremental drift on sensor_b: the mean shifts linearly from 30 to 50 over the transition period.
    Recurring drift on status: the classification boundary periodically alternates between two formulas at configurable intervals.

    Parameters
    ----------
    seed
        Random seed for reproducibility

    Examples
    --------
    >>> from sdg.generators.drifttypesdemo import DriftTypesDemo

    >>> gen = DriftTypesDemo(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    sensor_a : float
        Primary sensor reading; drifts gradually from N(50,5) to N(70,5)
    sensor_b : float
        Secondary sensor reading; drifts incrementally from mean 30 to mean 50
    noise : float
        Additive Gaussian noise term
    Target
    ------
    status : Binary
        System status: 0=normal, 1=warning. Classification boundary changes recurringly.

    Notes
    -----
    This is an infinite stream generator. Use `get_n_instances(n)` to get a
    finite number of samples, or iterate directly for infinite streaming.
    """

    DEFAULT_TRANSITION_STEPS = 100
    DEFAULT_RECURRING_INTERVAL = 1000
    DEFAULT_RECURRING_DURATION = 500

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: Random seed for reproducibility
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "DriftTypesDemo"
        self.feature_names = ["sensor_a", "sensor_b", "noise"]
        self.target_name = "status"
        self.drift_configs = {
            "sensor_a": {"types": ["gradual"], "n_scenarios": 2},
            "sensor_b": {"types": ["incremental"], "n_scenarios": 2},
            "status": {"types": ["recurring"], "n_scenarios": 2},
        }
        self._drift_state = {feature_key: [] for feature_key in self.drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "sensor_a":
            return self._rng.gauss(50, 5)
        elif name == "sensor_b":
            return self._rng.gauss(30, 3)
        elif name == "noise":
            return self._rng.gauss(0, 1)
        elif name == "status":
            return 1 if ((features_dict['sensor_a'] + features_dict['noise']) > 60) else 0
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "sensor_a":
            if scenario_index == 0:
                return self._rng.gauss(50, 5)
            elif scenario_index == 1:
                return self._rng.gauss(70, 5)
        elif name == "sensor_b":
            if scenario_index == 0:
                return self._rng.gauss(30, 3)
            elif scenario_index == 1:
                return self._rng.gauss(50, 3)
        elif name == "status":
            if scenario_index == 0:
                return 1 if ((features_dict['sensor_a'] + features_dict['noise']) > 60) else 0
            elif scenario_index == 1:
                return 1 if ((features_dict['sensor_b'] + features_dict['noise']) > 45) else 0
        raise ValueError(f"Unknown drift scenario: {name}[{scenario_index}]")

    def add_drift(
        self,
        feature_name,
        drift_type=None,
        scenario_idx=None,
        transition_steps=None,
        interval=None,
        duration=None,
    ):
        """Apply drift immediately for a feature or target variable.

        Use this method to activate a drift starting at the current instance
        count (self._instance_count). For 'sudden' and 'recurring' drifts the
        generator switches to the chosen scenario immediately; for 'gradual'
        and 'incremental' a transition occurs over `transition_steps` samples.
        If `scenario_idx` is None, a random non-zero scenario will be selected.
        For recurring drifts, `interval` and `duration` control periodic activation.

        Parameters
        ----------
        feature_name
            Name of the feature or target to apply drift to.
        drift_type
            Type of drift to apply (e.g., 'sudden', 'gradual', 'incremental', 'recurring').
        scenario_idx
            Index of the drift scenario to use (None selects random scenario).
        transition_steps
            Number of instances over which to transition (for gradual/incremental).
        interval, duration
            Interval and duration (for recurring drifts).
        """
        if feature_name not in self.drift_configs:
            raise ValueError(f"No drift config for '{feature_name}'")
        cfg = self.drift_configs[feature_name]
        drift_type = drift_type or "sudden"
        if cfg["types"] and drift_type not in cfg["types"]:
            raise ValueError(f"Drift type '{drift_type}' not allowed for '{feature_name}'")
        if scenario_idx is not None and (scenario_idx < 0 or scenario_idx >= cfg["n_scenarios"]):
            raise ValueError(f"Invalid scenario index {scenario_idx}")
        current_scenario_index = (
            scenario_idx
            if scenario_idx is not None
            else self._rng.randint(1, cfg["n_scenarios"] - 1)
        )
        drift_state = {
            "active": True,
            "drift_point": self._instance_count,
            "drift_type": drift_type,
            "scenario_index_config": scenario_idx,
            "current_scenario_index": current_scenario_index,
        }
        drift_state["transition_steps"] = transition_steps or self.DEFAULT_TRANSITION_STEPS
        drift_state["transition_progress"] = 0
        drift_state["recurring_interval"] = interval or self.DEFAULT_RECURRING_INTERVAL
        drift_state["recurring_duration"] = duration or self.DEFAULT_RECURRING_DURATION
        drift_state["recurring_start"] = self._instance_count
        self._drift_state[feature_name].append(drift_state)

    def _check_drifts(self):
        for feature_name, drift_states in self._drift_state.items():
            for drift_state in drift_states:
                if (
                    drift_state["active"]
                    and drift_state["drift_type"] == "recurring"
                    and self._instance_count - drift_state["recurring_start"]
                    >= drift_state["recurring_duration"]
                ):
                    drift_state["active"] = False

    def _get_val(self, name, features_dict):
        """Get value considering drift."""
        active_drift = next(
            (
                drift_state
                for drift_state in reversed(self._drift_state.get(name, []))
                if drift_state["active"]
            ),
            None,
        )
        if not active_drift:
            return self._gen(name, features_dict)
        drift_type = active_drift["drift_type"]
        current_scenario_index = active_drift["current_scenario_index"]

        if drift_type in ("sudden", "recurring"):
            return self._scenario(name, current_scenario_index, features_dict)
        if drift_type in ("gradual", "incremental"):
            # if transition completed, use drift scenario
            if active_drift["transition_progress"] >= active_drift["transition_steps"]:
                return self._scenario(name, current_scenario_index, features_dict)

            transition_ratio = (
                active_drift["transition_progress"] / active_drift["transition_steps"]
            )
            active_drift["transition_progress"] += 1

            if drift_type == "gradual":
                # probabilistic switch: use drift scenario with probability=transition_ratio
                return (
                    self._scenario(name, current_scenario_index, features_dict)
                    if self._rng.random() < transition_ratio
                    else self._gen(name, features_dict)
                )

            # incremental: interpolate between default and drift
            return (1 - transition_ratio) * self._gen(
                name, features_dict
            ) + transition_ratio * self._scenario(name, current_scenario_index, features_dict)

        return self._scenario(name, current_scenario_index, features_dict)

    def get_drift_info(self):
        """Return drift configuration and state."""
        return {
            feature_name: {
                "types": config["types"],
                "n_scenarios": config["n_scenarios"],
                "drifts": [
                    {
                        "active": drift_state["active"],
                        "drift_type": drift_state["drift_type"],
                        "scenario_idx": drift_state["current_scenario_index"],
                        "drift_point": drift_state["drift_point"],
                    }
                    for drift_state in self._drift_state[feature_name]
                ],
            }
            for feature_name, config in self.drift_configs.items()
        }

    def __iter__(self):
        while True:
            self._check_drifts()
            features_dict = {}
            for feature_name in self.feature_names:
                features_dict[feature_name] = (
                    self._get_val(feature_name, features_dict)
                    if feature_name in self._drift_state
                    else self._gen(feature_name, features_dict)
                )
            target_value = self._get_val(self.target_name, features_dict)
            self._instance_count += 1
            yield [features_dict[feature_name] for feature_name in self.feature_names], target_value

    def get_n_instances(self, n_instances):
        return itertools.islice(self, n_instances)

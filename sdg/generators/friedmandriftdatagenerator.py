import random
import itertools
import math


class FriedmanDataGenerator:
    """
    FriedmanDataGenerator stream generator.

    Stream generator introduced by Friedman

    Relevant paper:
    Friedman, Jerome H. Multivariate Adaptive Regression Splines. The Annals of Statistics 19.1 (1991): 1-141.
    Available online: http://www.stat.yale.edu/~lc436/08Spring665/Mars_Friedman_91.pdf

    Parameters
    ----------
    seed
        The seed of the random generator

    Examples
    --------
    >>> from sdg.generators.friedmandatagenerator import FriedmanDataGenerator

    >>> gen = FriedmanDataGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    x1 : float
        The first variable
    x2 : float
        The second variable
    x3 : float
        The third variable
    x4 : float
        The fourth variable
    x5 : float
        The fifth variable
    x6 : float
        The sixth variable
    x7 : float
        The seventh variable
    x8 : float
        The eighth variable
    x9 : float
        The ninth variable
    x10 : float
        The tenth variable
    noise : float
        Noise of the target

    Target
    ------
    y : Scalar
        The target variable defined as a function of the features

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
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "FriedmanDataGenerator"
        self.feature_names = [
            "x1",
            "x2",
            "x3",
            "x4",
            "x5",
            "x6",
            "x7",
            "x8",
            "x9",
            "x10",
            "noise",
        ]
        self.target_name = "y"
        self._drift_configs = {
            "y": {"types": ["gradual", "sudden", "recurring"], "n_scenarios": 5},
        }
        self._drift_state = {feature_key: [] for feature_key in self._drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "x1":
            return self._rng.uniform(0, 1)
        elif name == "x2":
            return self._rng.uniform(0, 1)
        elif name == "x3":
            return self._rng.uniform(0, 1)
        elif name == "x4":
            return self._rng.uniform(0, 1)
        elif name == "x5":
            return self._rng.uniform(0, 1)
        elif name == "x6":
            return self._rng.uniform(0, 1)
        elif name == "x7":
            return self._rng.uniform(0, 1)
        elif name == "x8":
            return self._rng.uniform(0, 1)
        elif name == "x9":
            return self._rng.uniform(0, 1)
        elif name == "x10":
            return self._rng.uniform(0, 1)
        elif name == "noise":
            return self._rng.gauss(0, 1)
        elif name == "y":
            return (
                10 * math.sin(math.pi * features_dict["x1"] * features_dict["x2"])
                + 20 * (features_dict["x3"] - 0.5) ** 2
                + 10 * features_dict["x4"]
                + 5 * features_dict["x5"]
                + features_dict["noise"]
            )
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "y":
            if scenario_index == 0:
                return (
                    10 * math.sin(math.pi * features_dict["x1"] * features_dict["x2"])
                    + 20 * (features_dict["x3"] - 0.5) ** 2
                    + 10 * features_dict["x4"]
                    + 5 * features_dict["x5"]
                    + features_dict["noise"]
                )
            elif scenario_index == 1:
                return (
                    10 * math.sin(math.pi * features_dict["x4"] * features_dict["x5"])
                    + 20 * (features_dict["x2"] - 0.5) ** 2
                    + 10 * features_dict["x1"]
                    + 5 * features_dict["x3"]
                    + features_dict["noise"]
                )
            elif scenario_index == 2:
                return (
                    10 * math.sin(math.pi * features_dict["x2"] * features_dict["x5"])
                    + 20 * (features_dict["x4"] - 0.5) ** 2
                    + 10 * features_dict["x3"]
                    + 5 * features_dict["x1"]
                    + features_dict["noise"]
                )
            elif scenario_index == 3:
                return (
                    (
                        10 * features_dict["x1"] * features_dict["x2"]
                        + 20 * (features_dict["x3"] - 0.5)
                        + 10 * features_dict["x4"]
                        + 5 * features_dict["x5"]
                        + features_dict["noise"]
                    )
                    if (features_dict["x2"] < 0.3 and features_dict["x3"] < 0.3)
                    else (
                        10
                        * math.sin(math.pi * features_dict["x1"] * features_dict["x2"])
                        + 20 * (features_dict["x3"] - 0.5) ** 2
                        + 10 * features_dict["x4"]
                        + 5 * features_dict["x5"]
                        + features_dict["noise"]
                    )
                )
            elif scenario_index == 4:
                return (
                    (
                        10 * math.cos(features_dict["x1"] * features_dict["x2"])
                        + 20 * (features_dict["x3"] - 0.5)
                        + math.exp(features_dict["x4"])
                        + 5 * features_dict["x5"] ** 2
                        + features_dict["noise"]
                    )
                    if (features_dict["x2"] > 0.7 and features_dict["x3"] > 0.7)
                    else (
                        10
                        * math.sin(math.pi * features_dict["x1"] * features_dict["x2"])
                        + 20 * (features_dict["x3"] - 0.5) ** 2
                        + 10 * features_dict["x4"]
                        + 5 * features_dict["x5"]
                        + features_dict["noise"]
                    )
                )
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
        if feature_name not in self._drift_configs:
            raise ValueError(f"No drift config for '{feature_name}'")
        cfg = self._drift_configs[feature_name]
        drift_type = drift_type or "sudden"
        if cfg["types"] and drift_type not in cfg["types"]:
            raise ValueError(
                f"Drift type '{drift_type}' not allowed for '{feature_name}'"
            )
        if scenario_idx is not None and (
            scenario_idx < 0 or scenario_idx >= cfg["n_scenarios"]
        ):
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
        drift_state["transition_steps"] = (
            transition_steps or self.DEFAULT_TRANSITION_STEPS
        )
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
            ) + transition_ratio * self._scenario(
                name, current_scenario_index, features_dict
            )

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
            for feature_name, config in self._drift_configs.items()
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
            yield (
                [features_dict[feature_name] for feature_name in self.feature_names],
                target_value,
            )

    def get_n_instances(self, n_instances):
        return itertools.islice(self, n_instances)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FriedmanDataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)

    args = parser.parse_args()

    gen = FriedmanDataGenerator(seed=args.seed)

    for X, y in gen.get_n_instances(args.samples):
        print(f"Instance {gen._instance_count}: X={X}, y={y}")

        if gen._instance_count == 140:
            drift_configs = getattr(gen, "_drift_configs", {})
            keys = list(drift_configs.keys())
            if keys:
                var = keys[0]
                cfg = drift_configs[var]
                types = cfg.get("types") if isinstance(cfg, dict) else None
                if types:
                    first_type = types[0] if len(types) else None
                    if first_type:
                        gen.add_drift(var, drift_type=first_type)
                        print(f"Added {first_type} drift on {var}")

import random
import itertools
import math


class MixedDataGenerator:
    """
    MixedDataGenerator stream generator.

    Mixed data stream generator with abrupt concept drift.

    This generator implements a data stream with abrupt concept drift and boolean noise-free examples as described in Gama et al. (2004).

    It has four relevant attributes: two boolean attributes (v, w) and two numeric attributes (x, y) uniformly distributed from 0 to 1.

    Classification function 0 (default):
    if (v and w) or (v and z) or (w and z) then 0 else 1

    Classification function 1 (drifted):
    if (v == 1 and w == 1) or (v == 1 and z) or (w == 1 and z) then 1 else 0

    where z = y < 0.5 + 0.3 * sin(3 * Ï * x)

    Concept drift can be introduced by switching between the two classification functions.

    Parameters
    ----------
    seed
        Random seed for reproducibility

    Examples
    --------
    >>> from sdg.generators.mixeddatagenerator import MixedDataGenerator

    >>> gen = MixedDataGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    v : bool
        Boolean attribute v (0 or 1 with equal probability)
    w : bool
        Boolean attribute w (0 or 1 with equal probability)
    x : float
        Numeric attribute x uniformly distributed from 0 to 1
    y : float
        Numeric attribute y uniformly distributed from 0 to 1

    Target
    ------
    classification : Binary
        Binary classification based on the selected classification function

    Notes
    -----
    This is an infinite stream generator. Use `get_n_instances(n)` to get a
    finite number of samples, or iterate directly for infinite streaming.
    """

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: Random seed for reproducibility
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "MixedDataGenerator"
        self.feature_names = ["v", "w", "x", "y"]
        self.target_name = "classification"
        self._drift_configs = {
            "classification": {"types": ["sudden"], "n_scenarios": 2},
        }
        self._drift_state = {feature_key: [] for feature_key in self._drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "v":
            return self._rng.uniform(0, 1) >= 0.5
        elif name == "w":
            return self._rng.uniform(0, 1) >= 0.5
        elif name == "x":
            return self._rng.uniform(0, 1)
        elif name == "y":
            return self._rng.uniform(0, 1)
        elif name == "classification":
            return (
                1
                if (
                    0
                    if (features_dict["v"] and features_dict["w"])
                    or (
                        features_dict["v"]
                        and (
                            features_dict["y"]
                            < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                        )
                    )
                    or (
                        features_dict["w"]
                        and (
                            features_dict["y"]
                            < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                        )
                    )
                    else 1
                )
                else 0
            )
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "classification":
            if scenario_index == 0:
                return (
                    1
                    if (
                        0
                        if (features_dict["v"] and features_dict["w"])
                        or (
                            features_dict["v"]
                            and (
                                features_dict["y"]
                                < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                            )
                        )
                        or (
                            features_dict["w"]
                            and (
                                features_dict["y"]
                                < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                            )
                        )
                        else 1
                    )
                    else 0
                )
            elif scenario_index == 1:
                return (
                    1
                    if (
                        1
                        if (features_dict["v"] and features_dict["w"])
                        or (
                            features_dict["v"]
                            and (
                                features_dict["y"]
                                < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                            )
                        )
                        or (
                            features_dict["w"]
                            and (
                                features_dict["y"]
                                < 0.5 + 0.3 * math.sin(3 * math.pi * features_dict["x"])
                            )
                        )
                        else 0
                    )
                    else 0
                )
        raise ValueError(f"Unknown drift scenario: {name}[{scenario_index}]")

    def add_drift(self, feature_name, drift_type=None, scenario_idx=None):
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
        self._drift_state[feature_name].append(drift_state)

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

    parser = argparse.ArgumentParser(description="MixedDataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)

    args = parser.parse_args()

    gen = MixedDataGenerator(seed=args.seed)

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

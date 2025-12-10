import random
import itertools


class StaggerDataGenerator:
    """
    StaggerDataGenerator stream generator.

    Stream generator producing three boolean features describing objects:
    size, shape and colour. Dataset originally introduced in:
    Schlimmer, J. C., & Granger, R. H. (1986). Incremental learning from.
    noisy data. Machine learning, 1(3), 317-354.

    Parameters
    ----------
    seed
        The seed of the random generator

    Examples
    --------
    >>> from sdg.generators.staggerdatagenerator import StaggerDataGenerator

    >>> gen = StaggerDataGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    size : string
        The size of the object, one of small, medium, large
    shape : string
        The shape of the object, one of circle, square, triangle
    color : string
        The color of the object, one of red, blue, green

    Target
    ------
    y : Binary
        The target variable defined as a function of the features

    Notes
    -----
    This is an infinite stream generator. Use `get_n_instances(n)` to get a
    finite number of samples, or iterate directly for infinite streaming.
    """

    DEFAULT_TRANSITION_STEPS = 100

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "StaggerDataGenerator"
        self.feature_names = ["size", "shape", "color"]
        self.target_name = "y"
        self._drift_configs = {
            "y": {"types": ["sudden", "gradual"], "n_scenarios": 3},
        }
        self._drift_state = {feature_key: [] for feature_key in self._drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "size":
            return self._rng.choice(["small", "medium", "large"])
        elif name == "shape":
            return self._rng.choice(["circle", "square", "triangle"])
        elif name == "color":
            return self._rng.choice(["red", "blue", "green"])
        elif name == "y":
            return (
                1
                if (
                    features_dict["size"] == "small" and features_dict["color"] == "red"
                )
                else 0
            )
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "y":
            if scenario_index == 0:
                return (
                    1
                    if (
                        features_dict["size"] == "small"
                        and features_dict["color"] == "red"
                    )
                    else 0
                )
            elif scenario_index == 1:
                return (
                    1
                    if (
                        features_dict["color"] == "green"
                        or features_dict["shape"] == "circle"
                    )
                    else 0
                )
            elif scenario_index == 2:
                return (
                    1
                    if (
                        features_dict["size"] == "medium"
                        or features_dict["size"] == "large"
                    )
                    else 0
                )
        raise ValueError(f"Unknown drift scenario: {name}[{scenario_index}]")

    def add_drift(
        self,
        feature_name,
        drift_points,
        drift_type=None,
        scenario_idx=None,
        transition_steps=None,
    ):
        """Configure concept drift for a feature or target variable."""
        if feature_name not in self._drift_configs:
            raise ValueError(f"No drift config for '{feature_name}'")
        cfg = self._drift_configs[feature_name]
        drift_points = [drift_points] if isinstance(drift_points, int) else drift_points
        drift_types = (
            [drift_type or "sudden"] * len(drift_points)
            if not isinstance(drift_type, list)
            else drift_type
        )
        scenario_indices = (
            [scenario_idx] * len(drift_points)
            if not isinstance(scenario_idx, list)
            else scenario_idx
        )

        for drift_point, drift_type, scenario_index in zip(
            drift_points, drift_types, scenario_indices
        ):
            if cfg["types"] and drift_type not in cfg["types"]:
                raise ValueError(
                    f"Drift type '{drift_type}' not allowed for '{feature_name}'"
                )
            if scenario_index is not None and (
                scenario_index < 0 or scenario_index >= cfg["n_scenarios"]
            ):
                raise ValueError(f"Invalid scenario index {scenario_index}")
            drift_state = {
                "active": False,
                "drift_point": drift_point,
                "drift_type": drift_type,
                "scenario_index_config": scenario_index,
                "current_scenario_index": 0,
            }
            drift_state["transition_steps"] = (
                transition_steps or self.DEFAULT_TRANSITION_STEPS
            )
            drift_state["transition_progress"] = 0
            self._drift_state[feature_name].append(drift_state)
        self._drift_state[feature_name].sort(
            key=lambda drift_state_item: drift_state_item["drift_point"]
        )

    def _check_drifts(self):
        for feature_name, drift_states in self._drift_state.items():
            for drift_state in drift_states:
                if self._instance_count == drift_state["drift_point"]:
                    drift_state["active"], drift_state["current_scenario_index"] = (
                        True,
                        drift_state["scenario_index_config"]
                        if drift_state["scenario_index_config"] is not None
                        else self._rng.randint(
                            1, self._drift_configs[feature_name]["n_scenarios"] - 1
                        ),
                    )
                    if drift_state["drift_type"] in ("gradual", "incremental"):
                        drift_state["transition_progress"] = 0

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

    parser = argparse.ArgumentParser(description="StaggerDataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)
    args = parser.parse_args()
    gen = StaggerDataGenerator(seed=args.seed)
    for i, (X, y) in enumerate(gen.get_n_instances(args.samples)):
        print(f"Instance {i}: X={X}, y={y}")

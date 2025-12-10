import random
import itertools


class Agrawal0DataGenerator:
    """
    Agrawal0DataGenerator stream generator.

    Stream generator introduced by Agrawal et al.

    Relevant paper:
    Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).
    An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).
    Available online: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf

    Parameters
    ----------
    seed
        The seed of the random generator

    Examples
    --------
    >>> from sdg.generators.agrawal0datagenerator import Agrawal0DataGenerator

    >>> gen = Agrawal0DataGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    salary : float
        Annual salary (uniformly sampled between 20,000 and 150,000).
    commission : float
        Commission income in USD: zero for salaries below 75,000; for higher salaries a uniform random value between 10,000 and 75,000.
    age : int
        Age of the individual in years (uniform integer between 20 and 80).
    educationlevel : int
        Education level code (integer 0â4) representing ascending educational attainment.
    car : int
        Car manufacturer ID (integer between 1 and 20), representing the maker of the individual's vehicle.
    zipcode : int
        Zip code region index of the individual's town (integer 0â8), used to influence house values.
    housevalue : float
        Estimated house value in USD, proportional to zipcode; uniformly sampled between 50,000 * zipcode and 100,000 * zipcode.
    houseyears : int
        Number of years the house has been owned (uniform integer between 1 and 30).
    loan : float
        Total outstanding loan amount (uniformly sampled between 0 and 500,000).

    Target
    ------
    loanapproval : Binary
        Loan Approval (classification function 0 of the original paper is used)

    Notes
    -----
    This is an infinite stream generator. Use `get_n_instances(n)` to get a
    finite number of samples, or iterate directly for infinite streaming.
    """

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "Agrawal0DataGenerator"
        self.feature_names = [
            "salary",
            "commission",
            "age",
            "educationlevel",
            "car",
            "zipcode",
            "housevalue",
            "houseyears",
            "loan",
        ]
        self.target_name = "loanapproval"
        self._drift_configs = {
            "loanapproval": {"types": ["sudden"], "n_scenarios": 2},
        }
        self._drift_state = {feature_key: [] for feature_key in self._drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "salary":
            return self._rng.uniform(20000, 150000)
        elif name == "commission":
            return (
                0
                if features_dict["salary"] < 75000
                else self._rng.uniform(10000, 75000)
            )
        elif name == "age":
            return self._rng.randint(20, 80)
        elif name == "educationlevel":
            return self._rng.randint(0, 4)
        elif name == "car":
            return self._rng.randint(1, 20)
        elif name == "zipcode":
            return self._rng.randint(0, 8)
        elif name == "housevalue":
            return self._rng.uniform(
                50000 * features_dict["zipcode"], 100000 * features_dict["zipcode"]
            )
        elif name == "houseyears":
            return self._rng.randint(1, 30)
        elif name == "loan":
            return self._rng.uniform(0, 500000)
        elif name == "loanapproval":
            return 1 if (features_dict["age"] < 40 or 60 <= features_dict["age"]) else 0
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "loanapproval":
            if scenario_index == 0:
                return (
                    1
                    if (features_dict["age"] < 40 or 60 <= features_dict["age"])
                    else 0
                )
            elif scenario_index == 1:
                return (
                    1
                    if (
                        (
                            features_dict["age"] < 40
                            and 50000 <= features_dict["salary"]
                            and features_dict["salary"] <= 100000
                        )
                        or (
                            features_dict["age"] < 60
                            and 75000 <= features_dict["salary"]
                            and features_dict["salary"] <= 125000
                        )
                        or (
                            25000 <= features_dict["salary"]
                            and features_dict["salary"] <= 75000
                        )
                    )
                    else 0
                )
        raise ValueError(f"Unknown drift scenario: {name}[{scenario_index}]")

    def add_drift(self, feature_name, drift_points, drift_type=None, scenario_idx=None):
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

    parser = argparse.ArgumentParser(description="Agrawal0DataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)
    args = parser.parse_args()
    gen = Agrawal0DataGenerator(seed=args.seed)
    for i, (X, y) in enumerate(gen.get_n_instances(args.samples)):
        print(f"Instance {i}: X={X}, y={y}")

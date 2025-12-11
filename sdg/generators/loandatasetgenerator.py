import random
import itertools


class LoanDatasetStreamGenerator:
    """
    LoanDatasetStreamGenerator stream generator.

    A stream generator for loans, introduced in publication:
    Kalaitzidis, E., Diamantopoulos, T., Michailoudis, A., Symeonidis, A. L. (2025).
    AML4S: An AutoML Pipeline for Data Streams. Machine Learning and Knowledge Extraction 7.3, 87.
    This generator is based on the generator introduced by Agrawal et al.
    (Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).
    An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).
    Available: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf.)

    Parameters
    ----------
    seed
        The seed of the random generator

    Examples
    --------
    >>> from sdg.generators.loandatasetstreamgenerator import LoanDatasetStreamGenerator

    >>> gen = LoanDatasetStreamGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    salary : float
        Salary
    commission : float
        Commission
    age : int
        Age
    educationlevel : int
        Education Level
    zipcode : int
        Zip Code of the Town
    housevalue : float
        House Value
    loanyears : int
        Years of the Loan
    loan : float
        Total Loan Amount

    Target
    ------
    loanapproval : Binary
        Loan Approval

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
        self.dataset_name = "LoanDatasetStreamGenerator"
        self.feature_names = [
            "salary",
            "commission",
            "age",
            "educationlevel",
            "zipcode",
            "housevalue",
            "loanyears",
            "loan",
        ]
        self.target_name = "loanapproval"
        self._drift_configs = {
            "salary": {"types": ["sudden"], "n_scenarios": 3},
            "loanapproval": {"types": ["sudden"], "n_scenarios": 3},
        }
        self._drift_state = {feature_key: [] for feature_key in self._drift_configs}

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "salary":
            return self._rng.uniform(20000, 60000)
        elif name == "commission":
            return self._rng.uniform(0, 0.1 * features_dict["salary"])
        elif name == "age":
            return self._rng.randint(20, 80)
        elif name == "educationlevel":
            return self._rng.randint(0, 4)
        elif name == "zipcode":
            return self._rng.randint(0, 8)
        elif name == "housevalue":
            return self._rng.uniform(
                100000 * (8 - features_dict["zipcode"] + 1),
                2 * 100000 * (8 - features_dict["zipcode"] + 1),
            )
        elif name == "loanyears":
            return self._rng.randint(10, 30)
        elif name == "loan":
            return self._rng.uniform(10000, 0.85 * features_dict["housevalue"])
        elif name == "loanapproval":
            return (
                1
                if (
                    (
                        features_dict["loan"]
                        <= 20 * features_dict["salary"]
                        + 0.5 * features_dict["commission"]
                    )
                    and (features_dict["loan"] <= 0.7 * features_dict["housevalue"])
                    and (
                        (
                            features_dict["age"] < 20
                            and features_dict["salary"]
                            + 0.5 * features_dict["commission"]
                            >= 20000
                        )
                        or (
                            features_dict["age"] < 40
                            and features_dict["salary"]
                            + 0.5 * features_dict["commission"]
                            >= 25000
                        )
                        or (
                            features_dict["age"] < 60
                            and features_dict["salary"]
                            + 0.5 * features_dict["commission"]
                            >= 30000
                        )
                    )
                )
                else 0
            )
        raise ValueError(f"Unknown feature or target: {name}")

    def _scenario(self, name, scenario_index, features_dict):
        """Get drift scenario value by name and index."""
        if name == "salary":
            if scenario_index == 0:
                return self._rng.uniform(20000, 60000)
            elif scenario_index == 1:
                return self._rng.uniform(10000, 40000)
            elif scenario_index == 2:
                return self._rng.uniform(30000, 80000)
        elif name == "loanapproval":
            if scenario_index == 0:
                return (
                    1
                    if (
                        (
                            features_dict["loan"]
                            <= 20 * features_dict["salary"]
                            + 0.5 * features_dict["commission"]
                        )
                        and (features_dict["loan"] <= 0.7 * features_dict["housevalue"])
                        and (
                            (
                                features_dict["age"] < 20
                                and features_dict["salary"]
                                + 0.5 * features_dict["commission"]
                                >= 20000
                            )
                            or (
                                features_dict["age"] < 40
                                and features_dict["salary"]
                                + 0.5 * features_dict["commission"]
                                >= 25000
                            )
                            or (
                                features_dict["age"] < 60
                                and features_dict["salary"]
                                + 0.5 * features_dict["commission"]
                                >= 30000
                            )
                        )
                    )
                    else 0
                )
            elif scenario_index == 1:
                return (
                    1
                    if (
                        (features_dict["loan"] <= 10 * features_dict["salary"])
                        and (features_dict["loan"] <= 0.5 * features_dict["housevalue"])
                        and (
                            (
                                features_dict["age"] < 20
                                and features_dict["salary"] >= 30000
                            )
                            or (
                                features_dict["age"] < 40
                                and features_dict["salary"] >= 40000
                            )
                            or (
                                features_dict["age"] < 60
                                and features_dict["salary"] >= 50000
                            )
                        )
                    )
                    else 0
                )
            elif scenario_index == 2:
                return (
                    1
                    if (
                        (
                            features_dict["loan"]
                            <= 50 * features_dict["salary"]
                            + features_dict["commission"]
                        )
                        and (features_dict["loan"] <= 0.9 * features_dict["housevalue"])
                        and (
                            (
                                features_dict["age"] < 20
                                and features_dict["salary"]
                                + features_dict["commission"]
                                >= 10000
                            )
                            or (
                                features_dict["age"] < 40
                                and features_dict["salary"]
                                + features_dict["commission"]
                                >= 15000
                            )
                            or (
                                features_dict["age"] < 60
                                and features_dict["salary"]
                                + features_dict["commission"]
                                >= 20000
                            )
                        )
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

    parser = argparse.ArgumentParser(description="LoanDatasetStreamGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)

    args = parser.parse_args()

    gen = LoanDatasetStreamGenerator(seed=args.seed)

    for X, y in gen.get_n_instances(args.samples):
        print(f"Instance {gen._instance_count}: X={X}, y={y}")

        if gen._instance_count == 100:
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

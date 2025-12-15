import random
import itertools


class MvDataGenerator:
    """
    MvDataGenerator stream generator.

    Mv artificial dataset.

    Artificial dataset composed of both nominal and numeric features, whose features present co-dependencies. Originally described by LuÃ­s Torgo.

    The features are generated using expressions with conditional logic and weighted random choices.

    Reference: https://www.dcc.fc.up.pt/~ltorgo/Regression/mv.html

    Parameters
    ----------
    seed
        Random seed number used for reproducibility

    Examples
    --------
    >>> from sdg.generators.mvdatagenerator import MvDataGenerator

    >>> gen = MvDataGenerator(seed=seed)
    >>> for X, y in gen.get_n_instances(500):
    ...     print(X, y)

    Features
    --------
    x1 : float
        Uniformly distributed over [-5, 5]
    x2 : float
        Uniformly distributed over [-15, -10]
    x3 : string
        Categorical: green if x1 > 0, else red (p=0.4) or brown (p=0.6)
    x4 : float
        Depends on x3: if green then x1 + 2*x2, else x1/2 (p=0.3) or x2/2 (p=0.7)
    x5 : float
        Uniformly distributed over [-1, 1]
    x6 : float
        x4 multiplied by epsilon uniformly distributed over [0, 5]
    x7 : string
        Categorical: yes (p=0.3) or no (p=0.7)
    x8 : string
        Categorical: normal if x5 < 0.5, else large
    x9 : float
        Uniformly distributed over [100, 500]
    x10 : float
        Uniformly distributed over [1000, 1200]

    Target
    ------
    y : Scalar
        Regression target with conditional rules based on feature values

    Notes
    -----
    This is an infinite stream generator. Use `get_n_instances(n)` to get a
    finite number of samples, or iterate directly for infinite streaming.
    """

    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: Random seed number used for reproducibility
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self._instance_count = 0
        self.dataset_name = "MvDataGenerator"
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
        ]
        self.target_name = "y"

    def _gen(self, name, features_dict):
        """Generate feature or target value by name."""
        if name == "x1":
            return self._rng.uniform(-5, 5)
        elif name == "x2":
            return self._rng.uniform(-15, -10)
        elif name == "x3":
            return (
                "green"
                if features_dict["x1"] > 0
                else ("red" if self._rng.uniform(0, 1) < 0.4 else "brown")
            )
        elif name == "x4":
            return (
                (features_dict["x1"] + 2 * features_dict["x2"])
                if features_dict["x3"] == "green"
                else (
                    features_dict["x1"] / 2
                    if self._rng.uniform(0, 1) < 0.3
                    else features_dict["x2"] / 2
                )
            )
        elif name == "x5":
            return self._rng.uniform(-1, 1)
        elif name == "x6":
            return features_dict["x4"] * self._rng.uniform(0, 5)
        elif name == "x7":
            return "yes" if self._rng.uniform(0, 1) < 0.3 else "no"
        elif name == "x8":
            return "normal" if features_dict["x5"] < 0.5 else "large"
        elif name == "x9":
            return self._rng.uniform(100, 500)
        elif name == "x10":
            return self._rng.uniform(1000, 1200)
        elif name == "y":
            return (
                (35 - 0.5 * features_dict["x4"])
                if features_dict["x2"] > 2
                else (
                    (10 - 2 * features_dict["x1"])
                    if (-2 <= features_dict["x4"] and features_dict["x4"] <= 2)
                    else (
                        (3 - features_dict["x1"] / features_dict["x4"])
                        if (features_dict["x7"] == "yes" and features_dict["x4"] != 0)
                        else (
                            (features_dict["x6"] + features_dict["x1"])
                            if features_dict["x8"] == "normal"
                            else (features_dict["x1"] / 2)
                        )
                    )
                )
            )
        raise ValueError(f"Unknown feature or target: {name}")

    def __iter__(self):
        while True:
            features_dict = {}
            for feature_name in self.feature_names:
                features_dict[feature_name] = self._gen(feature_name, features_dict)
            target_value = self._gen(self.target_name, features_dict)
            self._instance_count += 1
            yield (
                [features_dict[feature_name] for feature_name in self.feature_names],
                target_value,
            )

    def get_n_instances(self, n_instances):
        return itertools.islice(self, n_instances)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MvDataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)

    args = parser.parse_args()

    gen = MvDataGenerator(seed=args.seed)

    for X, y in gen.get_n_instances(args.samples):
        print(f"Instance {gen._instance_count}: X={X}, y={y}")

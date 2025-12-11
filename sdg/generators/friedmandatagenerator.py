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

    parser = argparse.ArgumentParser(description="FriedmanDataGenerator")
    parser.add_argument("--seed", type=type(42), default=42)
    parser.add_argument("--samples", type=int, default=150)

    args = parser.parse_args()

    gen = FriedmanDataGenerator(seed=args.seed)

    for X, y in gen.get_n_instances(args.samples):
        print(f"Instance {gen._instance_count}: X={X}, y={y}")

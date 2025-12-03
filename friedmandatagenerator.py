import random
import itertools
import math

class FriedmanDataGenerator:
    """
    Stream generator introduced by Friedman

 Relevant paper:
 Friedman, Jerome H. Multivariate Adaptive Regression Splines. The Annals of Statistics 19.1 (1991): 1-141.
 Available online: http://www.stat.yale.edu/~lc436/08Spring665/Mars_Friedman_91.pdf

    Features:
    - x1: The first variable
    - x2: The second variable
    - x3: The third variable
    - x4: The fourth variable
    - x5: The fifth variable
    - x6: The sixth variable
    - x7: The seventh variable
    - x8: The eighth variable
    - x9: The ninth variable
    - x10: The tenth variable
    - noise: Noise of the target

    Target:
    - y: The target variable defined as a function of the features
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
        self.feature_names = ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10", "noise"]
        self.target_name = "y"

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples (X, y): X is feature list, y is target.
        """
        while True:
            x1 = self._rng.uniform(0, 1)
            x2 = self._rng.uniform(0, 1)
            x3 = self._rng.uniform(0, 1)
            x4 = self._rng.uniform(0, 1)
            x5 = self._rng.uniform(0, 1)
            x6 = self._rng.uniform(0, 1)
            x7 = self._rng.uniform(0, 1)
            x8 = self._rng.uniform(0, 1)
            x9 = self._rng.uniform(0, 1)
            x10 = self._rng.uniform(0, 1)
            noise = self._rng.gauss(mu=0, sigma=1)
            y = 10 * math.sin(math.pi * x1 * x2) + 20 * (x3 - 0.5) ** 2 + 10 * x4 + 5 * x5 + noise

            self._instance_count += 1
            yield [x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, noise], y

    def get_n_instances(self, numinstances):
        """
        Generates and returns the number of data instances that is given as a parameter.
        """
        return itertools.islice(self, numinstances)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FriedmanDataGenerator - Stream Data Generator')
    parser.add_argument('--seed', type=type(42), default=42, help='The seed of the random generator')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    # Initialize generator with parsed arguments
    gen = FriedmanDataGenerator(seed=args.seed)
    
    # Generate and print samples
    for i, (X, y) in enumerate(gen):
        print(f"Instance {i}: X={X}, y={y}")
        if i >= args.samples - 1:
            break
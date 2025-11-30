import random
import itertools

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
    def __init__(self, seed):
        """
        Initializes this random data generator

        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self.y_function = self._y_function_0
        self.dataset_name = "StaggerDataGenerator"
        self.feature_names = ["size", "shape", "color"]
        self.target_name = "y"
        self.driftable_variables = {'y'}

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples of the format (X, y), where X is a list with feature
                  instances and y is the target instance.
        """
        while True:

            size = self._rng.choice(["small", "medium", "large"])
            shape = self._rng.choice(["circle", "square", "triangle"])
            color = self._rng.choice(["red", "blue", "green"])

            y = self.y_function(size, shape, color)
            yield [size, shape, color], y

    def get_n_instances(self, numinstances):
        """
        Generates and returns the number of data instances that is given as a parameter.

        :param numinstances: The number of instances to be returned
        :returns: A generator of tuples of the format (X, y), where is X is a list with feature
                  instances and y is the target instance
        """
        return itertools.islice(self, numinstances)

    def concept_drift(self):
        """
        Generates a concept drift by randomly choosing a
        generation function for the target variable.
        """
        self._drift("y")

    def _drift(self, variable):
        if variable == "y":
            newfunc = self.y_function
            while newfunc == self.y_function:
                self.y_function = self._rng.choice([self._y_function_0, self._y_function_1, self._y_function_2])

    def _y_function_0(self, size, shape, color):  # @UnusedVariable
        if size == "small" and color == "red":
            y = 1
        else:
            y = 0
        return y

    def _y_function_1(self, size, shape, color):  # @UnusedVariable
        if color == "green" or shape == "circle":
            y = 1
        else:
            y = 0
        return y

    def _y_function_2(self, size, shape, color):  # @UnusedVariable
        if size == "medium" or size == "large":
            y = 1
        else:
            y = 0
        return y

if __name__ == '__main__':
    # Example of running this data generator
    gen = StaggerDataGenerator(seed = 42)
    for i, (X, y) in enumerate(gen):
        print("Index: {} - X: {} - y: {}".format(i, X, y))

import random
import itertools
import math

class Agrawal0DataGenerator:
    """
    Stream generator introduced by Agrawal et al.\n\n Relevant paper:\n Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).\n An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).\n Available online: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf

    Features:
    - salary: Salary
    - commission: Commission
    - age: Age
    - educationlevel: Education Level
    - car: Car Maker
    - zipcode: Zip Code of the Town
    - housevalue: House Value
    - houseyears: Years House Owned
    - loan: Total Loan Amount

    Target:
    - loanapproval: Loan Approval (classification function 0 of the original paper is used)
    """
    def __init__(self, seed):
        """
        Initializes this random data generator
        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self.loanapproval_function = self._loanapproval_function_0
        self.dataset_name = "Agrawal0DataGenerator"
        self.feature_names = ["salary", "commission", "age", "educationlevel", "car", "zipcode", "housevalue", "houseyears", "loan"]
        self.target_name = "loanapproval"
        self.driftable_variables = {
            "loanapproval"
        }

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples of the format (X, y), where X is a list with feature
                  instances and y is the target instance.
        """
        while True:
            salary: float = self._rng.uniform(20000, 150000)
            commission: float = 0 if salary < 75000 else self._rng.uniform(10000, 75000)
            age: int = self._rng.randint(20, 80)
            educationlevel: int = self._rng.randint(0, 4)
            car: int = self._rng.randint(1, 20)
            zipcode: int = self._rng.randint(0, 8)
            housevalue: float = self._rng.uniform(50000 * zipcode, 100000 * zipcode)
            houseyears: int = self._rng.randint(1, 30)
            loan: float = self._rng.uniform(0, 500000)
            loanapproval = self.loanapproval_function(salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan)
            yield [salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan], loanapproval

    def get_n_instances(self, numinstances):
        """
        Generates and returns the number of data instances that is given as a parameter.

        :param numinstances: The number of instances to be returned
        :returns: A generator of tuples of the format (X, y), where is X is a list with feature
                  instances and y is the target instance
        """
        return itertools.islice(self, numinstances)
    def data_drift(self, feature):
        """
        Generates a data drift by randomly choosing a data
        generation function for the given variable.

        :param feature: the feature on which the data drift is performed
        """
        self._drift(feature)

    def concept_drift(self):
        """
        Generates a concept drift by randomly choosing a
        generation function for the target variable.
        """
        self._drift("loanapproval")

    def _drift(self, variable):
        if variable == "loanapproval":
            newfunc = self.loanapproval_function
            while newfunc == self.loanapproval_function:
                self.loanapproval_function = self._rng.choice([
                    self._loanapproval_function_0,
                    self._loanapproval_function_1,
                    self._loanapproval_function_2,
                ])
    def _loanapproval_function_0(self, salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan):  # @UnusedVariable
        if age < 40 or 60 <= age:
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval
    def _loanapproval_function_1(self, salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan):  # @UnusedVariable
        if age < 40 or 60 <= age:
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval
    def _loanapproval_function_2(self, salary, commission, age, educationlevel, car, zipcode, housevalue, houseyears, loan):  # @UnusedVariable
        if (age < 40 and 50000 <= salary and salary <= 100000) or (age < 60 and 75000 <= salary and salary <= 125000) or (25000 <= salary and salary <= 75000):
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Agrawal0DataGenerator - Stream Data Generator')
    parser.add_argument('--seed', type=type(42), default=42, help='The seed of the random generator')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    # Initialize generator with parsed arguments
    gen = Agrawal0DataGenerator(seed=args.seed)
    
    # Generate and print samples
    for i, (X, y) in enumerate(gen):
        print(f"Instance {i}: X={X}, y={y}")
        if i >= args.samples - 1:
            break
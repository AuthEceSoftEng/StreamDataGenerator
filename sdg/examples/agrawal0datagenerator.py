import random
import itertools

class Agrawal0DataGenerator:
    """
    Stream generator introduced by Agrawal et al.
    
    Relevant paper:
    Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).
    An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).
    Available online: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf

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
        self.driftable_variables = {'loanapproval'}

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples of the format (X, y), where X is a list with feature
                  instances and y is the target instance.
        """
        while True:

            salary = self._rng.uniform(20000, 150000)
            commission = 0 if salary < 75000 else self._rng.uniform(10000, 75000)
            age = self._rng.randint(20, 80)
            educationlevel = self._rng.randint(0, 4)
            car = self._rng.randint(1, 20)
            zipcode = self._rng.randint(0, 8)
            housevalue = self._rng.uniform(50000 * zipcode, 100000 * zipcode)
            houseyears = self._rng.randint(1, 30)
            loan = self._rng.uniform(0, 500000)

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
                self.loanapproval_function = self._rng.choice([self._loanapproval_function_0, self._loanapproval_function_1, self._loanapproval_function_2])

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
    # Example of running this data generator
    gen = Agrawal0DataGenerator(seed = 42)
    for i, (X, y) in enumerate(gen):
        print("Index: {} - X: {} - y: {}".format(i, X, y))

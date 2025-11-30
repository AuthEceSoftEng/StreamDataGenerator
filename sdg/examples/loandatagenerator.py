import random
import itertools

class LoanDatasetStreamGenerator:
    """
    A stream generator for loans, introduced in publication:
    Kalaitzidis, E., Diamantopoulos, T., Michailoudis, A., Symeonidis, A. L. (2025).
    AML4S: An AutoML Pipeline for Data Streams. Machine Learning and Knowledge Extraction 7.3, 87.
    This generator is based on the generator introduced by Agrawal et al.
    (Agrawal, R., Ghosh, S., Imielinski, T., Iyer, B., & Swami, A. N. (1992).
    An interval classifier for database mining applications. In VLDB (Vol. 92, pp. 560-573).
    Available: https://agrawal-family.com/rakesh/papers/vldb92ic.pdf.)

    Features:
    - salary: Salary
    - commission: Commission
    - age: Age
    - educationlevel: Education Level
    - zipcode: Zip Code of the Town
    - housevalue: House Value
    - loanyears: Years of the Loan
    - loan: Total Loan Amount

    Target:
    - loanapproval: Loan Approval
    """
    def __init__(self, seed):
        """
        Initializes this random data generator

        :param seed: The seed of the random generator
        """
        self.seed = seed
        self._rng = random.Random(self.seed)
        self.salary_function = self._salary_function_0
        self.loanapproval_function = self._loanapproval_function_0
        self.dataset_name = "LoanDatasetStreamGenerator"
        self.feature_names = ["salary", "commission", "age", "educationlevel", "zipcode", "housevalue", "loanyears", "loan"]
        self.target_name = "loanapproval"
        self.driftable_variables = {'loanapproval', 'salary'}

    def __iter__(self):
        """
        Generates and returns new data instances.

        :returns: A generator of tuples of the format (X, y), where X is a list with feature
                  instances and y is the target instance.
        """
        while True:
            salary = self.salary_function()
            commission = self._rng.uniform((0, 0.1 * salary))
            age = self._rng.randint(20, 80)
            educationlevel = self._rng.randint(0, 4)
            zipcode = self._rng.randint(0, 8)
            housevalue = self._rng.uniform((100000 * (8 - zipcode + 1), 2 * 100000 * (8 - zipcode + 1)))
            loanyears = self._rng.randint(10, 30)
            loan = self._rng.uniform((10000, 0.85 * housevalue))

            loanapproval = self.loanapproval_function(salary, commission, age, educationlevel, zipcode, housevalue, loanyears, loan)
            yield [salary, commission, age, educationlevel, zipcode, housevalue, loanyears, loan], loanapproval

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
        if variable == "salary":
            newfunc = self.salary_function
            while newfunc == self.salary_function:
                self.salary_function = self._rng.choice([self._salary_function_0, self._salary_function_1, self._salary_function_2])
        if variable == "loanapproval":
            newfunc = self.loanapproval_function
            while newfunc == self.loanapproval_function:
                self.loanapproval_function = self._rng.choice([self._loanapproval_function_0, self._loanapproval_function_1, self._loanapproval_function_2])

    def _salary_function_0(self):
        salary = self._rng.uniform((20000, 60000))
        return salary

    def _salary_function_1(self):
        salary = self._rng.uniform((10000, 40000))
        return salary

    def _salary_function_2(self):
        salary = self._rng.uniform((30000, 80000))
        return salary

    def _loanapproval_function_0(self, salary, commission, age, educationlevel, zipcode, housevalue, loanyears, loan):  # @UnusedVariable
        if (loan <= 20 * salary + 0.5 * commission) and (loan <= 0.7 * housevalue) and ((age < 20 and salary + 0.5 * commission >= 20000) or (age < 40 and salary + 0.5 * commission >= 25000) or (age < 60 and salary + 0.5 * commission >= 30000)):
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval

    def _loanapproval_function_1(self, salary, commission, age, educationlevel, zipcode, housevalue, loanyears, loan):  # @UnusedVariable
        if (loan <= 10 * salary) and (loan <= 0.5 * housevalue) and ((age < 20 and salary >= 30000) or (age < 40 and salary >= 40000) or (age < 60 and salary >= 50000)):
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval

    def _loanapproval_function_2(self, salary, commission, age, educationlevel, zipcode, housevalue, loanyears, loan):  # @UnusedVariable
        if (loan <= 50 * salary + commission) and (loan <= 0.9 * housevalue) and ((age < 20 and salary + commission >= 10000) or (age < 40 and salary + commission >= 15000) or (age < 60 and salary + commission >= 20000)):
            loanapproval = 1
        else:
            loanapproval = 0
        return loanapproval

if __name__ == '__main__':
    # Example of running this data generator
    gen = LoanDatasetStreamGenerator(seed = 42)
    for i, (X, y) in enumerate(gen):
        print("Index: {} - X: {} - y: {}".format(i, X, y))

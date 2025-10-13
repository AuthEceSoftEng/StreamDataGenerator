from random import seed, randint
from sdg.examples.loandatagenerator import LoanDatasetStreamGenerator

""" Set here the data generator (and import it in the code) """
DataGenerator = LoanDatasetStreamGenerator

""" Set here the number of instances """
datasize = 10000

""" Set here the random seed """
randomseed = 42
seed(randomseed)

""" Set here the concept drift positions """
""" If only their count is given, then they are produced randomly """
conceptdrifts = 4
if not isinstance(conceptdrifts, list):
    conceptdrifts = [randint(100, datasize - 100) for _ in range(0, conceptdrifts)]
numconceptdrifts = len(conceptdrifts)

""" Set here the data drift positions for each feature """
""" If only their count is given, then they are produced randomly """
datadrifts, numdatadrifts = {}, {}
datadrifts["salary"] = 4
if not isinstance(datadrifts["salary"], list):
    datadrifts["salary"] = [randint(100, datasize - 100) for _ in range(0, datadrifts["salary"])]
numdatadrifts["salary"] = len(datadrifts["salary"])

if __name__ == '__main__':
    gen = DataGenerator(seed = randomseed)
    print("Using data generator " + gen.dataset_name)
    print("Creating a dataset of " + str(datasize) + " instances")
    dataset = gen.get_n_instances(datasize)
    if numconceptdrifts > 0 and gen.target_name in gen.driftable_variables:
        print("    with " + str(numconceptdrifts) + " concept drifts")
    datadriftfeatures = [var for var in gen.driftable_variables if var != gen.target_name and var in datadrifts]
    for feature in datadriftfeatures:
        print("    with " + str(numconceptdrifts) + " data drifts for feature " + feature)
    print("\n")

    for i, (X, y) in enumerate(gen.get_n_instances(datasize)):
        if i in conceptdrifts:
            print("Concept drift at: %d" %i)
            gen.concept_drift()
        for feature in datadriftfeatures:
            if i in datadrifts[feature]:
                print("Data drift of feature %s at: %d" %(feature, i))
                gen.data_drift(feature)
        print("Index: {} - X: {} - y: {}".format(i, X, y))
    print("\n")

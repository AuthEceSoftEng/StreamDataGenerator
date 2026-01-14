from examples.loandatadescriptor import LoanDatasetStreamGenerator

""" Set here the data generator (and import it in the code) """
DataGenerator = LoanDatasetStreamGenerator

""" Set here the number of instances """
datasize = 10000

""" Set here the concept drift positions - leave empty for no concept drifts """
conceptdrifts = [1924, 509, 4606, 4112]
#conceptdrifts = []

""" Set here the data drift positions for each feature - leave empty for no data drifts """
datadrifts = {'salary': [3757, 2386, 1779, 9035]}
#datadrifts = {}

if __name__ == '__main__':
    gen = DataGenerator(seed = 42)
    print("Using data generator " + gen.dataset_name)
    print("Creating a dataset of " + str(datasize) + " instances")
    if len(conceptdrifts) > 0 and gen.target_name in getattr(gen, 'drift_configs', {}):
        print("    with " + str(len(conceptdrifts)) + " concept drifts")
    datadriftfeatures = [var for var in getattr(gen, 'drift_configs', {}) if var != gen.target_name and var in datadrifts]
    for feature in datadriftfeatures:
        print("    with " + str(len(datadrifts[feature])) + " data drifts for feature " + feature)
    print("\n")

    for i, (X, y) in enumerate(gen.get_n_instances(datasize)):
        if i in conceptdrifts:
            print("Concept drift at: %d" %i)
            gen.add_drift(gen.target_name)
        for feature in datadriftfeatures:
            if i in datadrifts[feature]:
                print("Data drift of feature %s at: %d" %(feature, i))
                gen.add_drift(feature)
        print("Index: {} - X: {} - y: {}".format(i, X, y))
    print("\n")

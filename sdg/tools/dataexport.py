import arffutils
import pandas as pd
from random import seed, randint
from sdg.examples.staggerdatagenerator import StaggerDataGenerator

""" Set here the data generator (and import it in the code) """
DataGenerator = StaggerDataGenerator

""" Set here the number of instances """
datasize = 10000

""" Set here the path to the output file, with extension .csv or .arff"""
output_file = "../examples/staggerdata10000.arff"

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

    data = []
    for i, (X, y) in enumerate(gen.get_n_instances(datasize)):
        if i in conceptdrifts:
            print("Concept drift at: %d" %i)
            gen.concept_drift()
        for feature in datadriftfeatures:
            if i in datadrifts[feature]:
                print("Data drift of feature %s at: %d" %(feature, i))
                gen.data_drift(feature)
        data.append(X + [y])
    print("\n")

    df = pd.DataFrame(data, columns = gen.feature_names + [gen.target_name])
    for column in df:
        # Infer if a column is categorical
        if df[column].dtype not in ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
            if 1.0 * df[column].nunique() / df[column].count() < 0.05:
                df[column] = df[column].astype('category')
        # Here one can override numerical columns that are categorical

    if output_file.endswith("csv"):
        df.to_csv(output_file, index=False)
    elif output_file.endswith("arff"):
        arffutils.pandas_dataframe_to_arff(df, output_file, gen.dataset_name)

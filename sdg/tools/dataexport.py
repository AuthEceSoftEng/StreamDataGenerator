import arffutils
import pandas as pd
from random import seed, randint
from sdg.examples.loandatagenerator import LoanDatasetStreamGenerator
from sdg.examples.staggerdatagenerator import StaggerDataGenerator

seed(42)
numconceptdrifts = 4
numdatadriftsperfeature = 4
datasize = 10000

# Set here the data generator
DataGenerator = StaggerDataGenerator

# Set here the path to the output
output_file = "../examples/staggerdata10000.arff"

if __name__ == '__main__':
    gen = DataGenerator(seed = 42)
    print("Using data generator " + gen.dataset_name)

    print("Creating a dataset of 10000 instances")
    dataset = gen.get_n_instances(datasize)

    if gen.target_name in gen.driftable_variables:
        conceptdrifts = [randint(100, datasize - 100) for _ in range(0, numconceptdrifts)]
        print("   To also add " + str(numconceptdrifts) + " concept drifts")
    datadriftfeatures = [var for var in gen.driftable_variables if var != gen.target_name]
    if len(datadriftfeatures) > 0:
        datadrifts = {}
        for feature in datadriftfeatures:
            datadrifts[feature] = [randint(100, datasize - 100) for _ in range(0, numdatadriftsperfeature)]
            print("   To also add " + str(numdatadriftsperfeature) + " data drifts for feature " + feature)
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
        # print("Index: {} - X: {} - y: {}".format(i, X, y))
    print("\n")

    df = pd.DataFrame(data, columns = gen.feature_names + [gen.target_name])
    for column in df:
        # Infer if a column is categorical
        if df[column].dtype not in ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
            if 1.0 * df[column].nunique() / df[column].count() < 0.05:
                df[column] = df[column].astype('category')

    if output_file.endswith("csv"):
        df.to_csv(output_file, index=False)
    elif output_file.endswith("arff"):
        arffutils.pandas_dataframe_to_arff(df, output_file, gen.dataset_name, gen.target_name)

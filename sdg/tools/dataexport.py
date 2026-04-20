import arffutils
import pandas as pd
from examples.loandatadescriptor import LoanDatasetStreamGenerator

""" Set here the path to the output file, with extension .csv or .arff"""
output_file = "../../examples/loandata.arff"

""" Set here the data (and import it in the code) """
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

    data = []
    for i, (X, y) in enumerate(gen.get_n_instances(datasize)):
        if i in conceptdrifts:
            print("Concept drift at: %d" %i)
            gen.add_drift(gen.target_name)
        for feature in datadriftfeatures:
            if i in datadrifts[feature]:
                print("Data drift of feature %s at: %d" %(feature, i))
                gen.add_drift(feature)
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

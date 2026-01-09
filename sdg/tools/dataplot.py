import pandas as pd
import matplotlib.pyplot as plt
from examples.mixeddatadescriptor import MixedDataGenerator

""" Set here the sampling size for the plot """
samplingsize = 100

""" Set here the data generator (and import it in the code) """
DataGenerator = MixedDataGenerator

""" Set here the number of instances """
datasize = 10000

""" Set here the concept drift positions """
""" If only their count is given, then they are produced randomly """
#conceptdrifts = [1924, 509, 4606, 4112]
conceptdrifts = []

""" Set here the data drift positions for each feature """
""" If only their count is given, then they are produced randomly """
#datadrifts = {'salary': [3757, 2386, 1779, 9035]}
datadrifts = {}

if __name__ == '__main__':
    gen = DataGenerator(seed = 42)
    print("Using data generator " + gen.dataset_name)
    print("Creating a dataset of " + str(datasize) + " instances")
    dataset = gen.get_n_instances(datasize)
    if len(conceptdrifts) > 0 and gen.target_name in getattr(gen, '_drift_configs', {}):
        print("    with " + str(len(conceptdrifts)) + " concept drifts")
    datadriftfeatures = [var for var in getattr(gen, '_drift_configs', {}) if var != gen.target_name and var in datadrifts]
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
    df = df.sample(n = samplingsize, random_state=42).sort_index()

    for column in df:
        # Infer if a column is categorical
        if df[column].dtype not in ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
            if 1.0 * df[column].nunique() / df[column].count() < 0.05:
                df[column] = df[column].astype('category')
    # Change categorical data to integers
    category_codes = {}
    for column in df:
        if df[column].dtype == "category":
            category_codes[column] = df[column].cat.categories
            df[column] = df[column].cat.codes

    axes = df.plot(subplots=True, figsize=(6.8, 6.2), color="#1f77b4", legend=False)
    for c, ax in enumerate(axes):
        cd, dd = [], []
        for i in conceptdrifts:
            cd = ax.axvline(i, ymin = -0.1, ymax = 1.1, clip_on=False, zorder=10, label = "Concept drifts", color = "red", linestyle = "dashed")
        for feature in datadriftfeatures:
            for i in [j for j in datadrifts[feature]]:
                dd = ax.axvline(i, ymin = -0.1, ymax = 1.1, clip_on=False, zorder=10, label = "Data drifts", color = "green", linestyle = "dotted", linewidth=1.75)
        ax.set_ylabel(df.columns[c], rotation=0, horizontalalignment='right', verticalalignment='center')
        if df.columns[c] in category_codes:
            ax.set_yticks(range(len(category_codes[df.columns[c]])))
            ax.set_yticklabels(list(category_codes[df.columns[c]]))
        else:
            ax.set_yticks([df[df.columns.values[c]].min(), df[df.columns.values[c]].max()])
            ax.ticklabel_format(useOffset=False, style='plain')
    drifts, driftnames = [], []
    drifts = [cd] if cd else []
    driftnames = ['Concept drifts'] if cd else []
    if dd: drifts.append(dd)
    if dd: driftnames.append('Data drifts')
    axes[0].legend(drifts, driftnames, loc = 'upper center', bbox_to_anchor=(0.5, 2.5), ncol=2)
    axes[-1].set_xlabel("Data instances")

    plt.tight_layout()
    plt.show()

import yaml
import regex
from sdg.generator.descriptorvalidation import validate_yaml

def _indent_code(code, indentation):
    indent = "\n" + "    " * indentation
    return indent + indent.join(code.split("\n"))

def _generate_uniform_float_distribution(rangemin, rangemax):
    return "self._rng.uniform(%s, %s)" %(rangemin, rangemax)

def _generate_uniform_integer_distribution(rangemin, rangemax):
    return "self._rng.randint(%s, %s)" %(rangemin, rangemax)

def _generate_gaussian_distribution(mu, sigma):
    return "self._rng.gauss(mu = %s, sigma = %s)" %(mu, sigma)

def _generate_categorical_random(categories):
    return "self._rng.choice([%s])" %(", ".join(categories))

def _add_feature(featurename, formulacode, return_statement = False):
    formulamatches = regex.finditer('(\w+)(?<rec>\((?:[^()]++|(?&rec))*\))', formulacode)
    for amatch in reversed(list(formulamatches)):
        matchspan = amatch.span()
        arguments = [arg.strip() for arg in amatch.group(2)[1:-1].split(',')]
        newformulacode = formulacode[:matchspan[0]]
        if amatch.group(1) == "Categorical":
            newformulacode += _generate_categorical_random(arguments)
        if amatch.group(1) == "UniformInteger":
            newformulacode += _generate_uniform_integer_distribution(*arguments)
        if amatch.group(1) == "UniformFloat":
            newformulacode += _generate_uniform_float_distribution(*arguments)
        if amatch.group(1) == "Gaussian":
            newformulacode += _generate_gaussian_distribution(*arguments)
        newformulacode += formulacode[matchspan[1]:]
    if return_statement:
        return _indent_code(featurename + " = " + newformulacode + "\nreturn " + featurename, 2)
    else:
        return _indent_code(featurename + " = " + newformulacode, 3)

def _generate_target_condition(conditions):
    conditional = ""
    if len(conditions) > 1:
        conditional += "("
        for condition in conditions[:-1]:
            conditional += "(" + condition + ") or\n"
    conditional += "(" + conditions[-1] + ")"
    if len(conditions) > 1:
        conditional += ")"
    return conditional

def _add_target(targetname, targettype, targetformula, return_statement = False):
    if targettype == "Binary":
        conditions = [cond.strip() for cond in targetformula.split(',')]
        targetcode = _generate_target_condition(conditions)
        newtargetcode = "if " + "\n                ".join(targetcode.split("\n")) + ":\n"
        newtargetcode += "    " + targetname + " = 1\n"
        newtargetcode += "else:\n"
        newtargetcode += "    " + targetname + " = 0"
    elif targettype == "Scalar":
        newtargetcode = "            " + targetname + " = " + targetformula + "\n"
    if return_statement:
        return _indent_code(newtargetcode + "\nreturn " + targetname, 2)
    else:
        return _indent_code(newtargetcode, 3)

def generate(yamlinput):
    clsoutput = ""
    description = [descline.strip() for descline in yamlinput["description"].strip().split("\n")] if "description" in yamlinput else ""
    params = yamlinput.get("parameters", [])
    imports = yamlinput.get("imports", [])
    features = yamlinput["features"]
    target = yamlinput["target"]

    # Add imports
    for i in ["random", "itertools"] + imports:
        clsoutput += "import " + i + "\n"

    # Add class (must have name, should have description)
    clsoutput += "\nclass " + yamlinput["name"] + ":\n"

    # Add comments
    clsoutput += '    """\n    ' + "\n    ".join(description) + "\n"
    clsoutput += "\n    Features:\n"
    # Add also features with descriptions in comment
    for feature in features:
        clsoutput += "    - " + feature["name"] + ": " + feature["description"] + "\n"
    # Add also target with description in comment
    clsoutput += "\n    Target:\n    - " + target["name"] + ": " + target["description"] + "\n"
    clsoutput += '    """\n'

    # Add __init__ method (parameters are optional)
    clsoutput += "    def __init__(" + ", ".join(["self"] + [param["name"] for param in params]) + "):\n"
    clsoutput += '        """\n        ' + "Initializes this random data generator\n\n"
    for param in params:
        clsoutput += "        :param " + param["name"] + ": " + param["description"] + "\n"
    clsoutput += '        """\n'
    clsoutput += "\n".join("        self." + param["name"] + " = " + param["name"] for param in params)
    clsoutput += "\n        self._rng = random.Random(self.seed)"
    for variable in [v for v in features + [target] if "drift" in v]:
        clsoutput += "\n        self." + variable["name"] + "_function = self._" + variable["name"] + "_function_0"
    # Add names and descriptions
    clsoutput += "\n        self.dataset_name = \"" + yamlinput["name"] + "\""
    clsoutput += "\n        self.feature_names = [\""
    for feature in features:
        clsoutput += feature["name"] + "\", \""
    clsoutput = clsoutput[:-3] + "]\n        self.target_name = \"" + target["name"] + "\""
    clsoutput += "\n        self.driftable_variables = " + str(set(v["name"] for v in features + [target] if "drift" in v))
    clsoutput += "\n"

    # Keep variable functions separately
    varfunctionnames = []
    varfunctions = []

    # Add __iter__ method
    clsoutput += "\n    def __iter__(self):\n"
    clsoutput += '        """\n        ' + "Generates and returns new data instances.\n\n"
    clsoutput += "        :returns: A generator of tuples of the format (X, y), where X is a list with feature\n" + \
                 "                  instances and y is the target instance.\n"
    clsoutput += '        """\n'
    clsoutput += "        while True:\n"
    # Code for features
    for feature in features:
        if "drift" in feature:
            clsoutput += "            " + feature["name"] + " = self." + feature["name"] + "_function()" 
            for f, formula in enumerate([feature["formula"]] + [df["value"] for df in feature["drift"]["formulas"]]):
                varfunctionnames.append("_" + feature["name"] + "_function_" + str(f))
                varfunctions.append("    def " + varfunctionnames[-1] + "(self):" + _add_feature(feature["name"], formula, True) + "\n")
        else:
            clsoutput += _add_feature(feature["name"], feature["formula"])
    clsoutput += "\n\n"
    # Code for target variable
    if "drift" in target:
        featurenames = ", ".join(feature["name"] for feature in features)
        clsoutput += "            " + target["name"] + " = self." + target["name"] + "_function(" + featurenames + ")\n" 
        for f, formula in enumerate([target["formula"]] + [df["value"] for df in target["drift"]["formulas"]]):
            varfunctionnames.append("_" + target["name"] + "_function_" + str(f))
            varfunctions.append("    def " + varfunctionnames[-1] + "(self, " + featurenames + "):  # @UnusedVariable" + _add_target(target["name"], target["classtype"], formula, True) + "\n")
    else:
        clsoutput += _add_target(target["name"], target["classtype"], target["formula"]) + "\n"
    # Code for returning
    clsoutput += "            yield [" + ", ".join(feature["name"] for feature in features) + "], " + target["name"] + "\n"

    # Add get_n_instances function
    clsoutput += "\n    def get_n_instances(self, numinstances):\n"
    clsoutput += '        """\n        ' + "Generates and returns the number of data instances that is given as a parameter.\n\n"
    clsoutput += "        :param numinstances: The number of instances to be returned\n"
    clsoutput += "        :returns: A generator of tuples of the format (X, y), where is X is a list with feature\n" + \
                 "                  instances and y is the target instance\n"
    clsoutput += '        """\n'
    clsoutput += "        return itertools.islice(self, numinstances)\n"

    # Add public drift functions
    clsoutput += "\n    def data_drift(self, feature):\n"
    clsoutput += '        """\n        ' + "Generates a data drift by randomly choosing a data\n"
    clsoutput += "        generation function for the given variable.\n\n"
    clsoutput += "        :param feature: the feature on which the data drift is performed\n"
    clsoutput += '        """\n'
    clsoutput += "        self._drift(feature)\n"
    clsoutput += "\n    def concept_drift(self):\n"
    clsoutput += '        """\n        ' + "Generates a concept drift by randomly choosing a\n"
    clsoutput += "        generation function for the target variable.\n"
    clsoutput += '        """\n'
    clsoutput += "        self._drift(\"" + target["name"] + "\")\n"

    # Add private drift function
    clsoutput += "\n    def _drift(self, variable):\n"
    for variable in [v for v in features + [target] if "drift" in v]:
        clsoutput += "        if variable == \"" + variable["name"] + "\":\n"
        clsoutput += "            newfunc = self." + variable["name"] + "_function\n"
        functionnames = ["self." + vfn for vfn in varfunctionnames if vfn[1:].split("_function_")[0] == variable["name"]]
        clsoutput += "            while newfunc == self." + variable["name"] + "_function:\n"
        clsoutput += "                self." + variable["name"] + "_function = self._rng.choice([" + ", ".join(functionnames) + "])\n"
    clsoutput += "\n"

    # Add variable functions
    for varfunction in varfunctions:
        clsoutput += varfunction + "\n"

    return clsoutput

def generate_run(yamlinput):
    if "run" in yamlinput:
        arguments = yamlinput["run"].get("arguments", [])
        runoutput = "if __name__ == '__main__':\n"
        runoutput += "    # Example of running this data generator\n"
        runoutput += "    gen = " + yamlinput["name"] + "("
        runoutput += ", ".join(argument["name"] + " = " + str(argument["value"]) for argument in arguments)
        runoutput += ")\n"
        runoutput += "    for i, (X, y) in enumerate(gen):\n"
        if "driftpositions" in yamlinput["run"]:
            for driftposition in yamlinput["run"]["driftpositions"]:
                runoutput += "        if " + " or ".join("i == " + str(position) for position in driftposition["positions"])
                runoutput += ":\n            gen." + driftposition["type"] + "_drift(" + ("\"" + driftposition["variable"] + "\"" if "variable" in driftposition else "") + ")\n"
        runoutput += "        print(\"Index: {} - X: {} - y: {}\".format(i, X, y))\n"
    return runoutput

if __name__ == '__main__':
    datasetname = "stagger"
    filename = "../examples/" + datasetname + "datadescriptor.yml"
    outputfilename = "../examples/" + datasetname + "datagenerator.py"

    # Read and validate yaml descriptor
    with open(filename) as infile:
        yamlinput = yaml.load(infile, Loader=yaml.FullLoader)["dataset"]
    validate_yaml(yamlinput)

    # Create dataset generator
    code = generate(yamlinput)

    # Create runner main function
    coderun = generate_run(yamlinput)

    with open(outputfilename, 'w') as outfile:
        outfile.write(code)
        outfile.write(coderun)

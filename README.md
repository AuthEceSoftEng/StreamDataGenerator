# Stream Data Generator DSL
SDG is a formal **Domain-Specific Language (DSL)** for describing stream dataset generators,
built using the [textX](https://textx.github.io/textX/) framework. This DSL provides a clean
and structured way to define data streams, including different feature (and target) variables
as well as drifts (data and concept).

The main features of SDG are:
- **Formal Grammar**: Robust syntax validation and error reporting.
- **Concise Syntax**: Write less code to describe complex datasets.
- **Type Safety**: Built-in validation for parameter types and formulas.
- **Code Generation**: Automatically generate Python code for data generation.
- **Tooling Support**: Integrated with the textX ecosystem (CLI, visualization).
- **Drift Support**: Native syntax for defining data and concept drifts (using formula variations).

## Installation
Clone the repository and install the package in **editable mode**. This ensures all dependencies
(including `textX` and `jinja2`) are installed correctly, while the installation also includes the
`textX[cli]` extras, enabling the standard `textx` command-line tools.

```bash
pip install -e .
```

## DSL Syntax
The DSL is designed to be readable and expressive. Blocks use explicit end markers.

### Example
```text
dataset LoanDataGenerator

    description: "Stream generator producing loan data"
    
    parameters
        seed: "The seed of the random generator"
    end_parameters
    
    features
        float salary: UniformFloat(20000, 150000), "Salary of the applicant"
        int age: UniformInteger(20, 80), "Age of the applicant"
    end_features
    
    target loanapproval:Binary
        description: "Loan Approval"
        formula: salary > 40000 and age <= 40
    end_target

    drifts
        drift on salary
            type: sudden
            scenarios
                UniformFloat(10000, 40000),
                UniformFloat(30000, 80000)
            end_scenarios
        end_drift
    end_drifts

end_dataset
```

### Language Constructs

#### Dataset
The top-level container for your generator definition.
```text
dataset MyGenerator
    ...
end_dataset
```

#### Parameters
Define input arguments that can be passed to the generator at runtime.
```text
parameters
    seed: "Random seed"
    noise: "Noise level"
end_parameters
```

#### Features
Define the input features (attributes) of the data stream.
Syntax: `[Type] name: formula[, "Description"]`
```text
features
    int age: UniformInteger(18, 90), "User Age"
    float income: Gaussian(50000, 10000), "Annual Income"
    string status: UniformCategorical("active", "inactive"), "Status"
end_features
```

Supported types for features are `int`, `float`, `string`, `bool`.

Supported functions are:
- `UniformFloat(min, max)`: Continuous uniform float between min and max
- `UniformInteger(min, max)`: Discrete uniform integer between min and max
- `Gaussian(mu, sigma)`: Normal distribution with mean and deviation
- `UniformCategorical("val1", "val2", ...)`: Uniform random choice among categorical values

#### Target
Define the target variable (label) for supervised learning tasks.
You must specify the type (`Binary`, `Float`, `Integer`, `Categorical`, `Scalar`).
```text
target churn: Binary
    description: "Customer Churn"
    formula: age > 60 and income < 30000
end_target
```

#### Drift
Define concept or data drifts by specifying alternative formulas for a feature or target.
Supported drift types include:
- `sudden`: rapid shift where a new concept replaces the old
- `gradual`: slow transition where old and new concepts temporarily coexist
- `incremental`: small continuous changes that accumulate into a significant shift
- `recurring`: concepts reappear periodically with seasonal patterns

Drift grammar example:
```text
drift on age
    type: sudden, gradual
    scenarios
        default: original_formula
        alternative: new_formula_after_drift
    end_scenarios
end_drift
```

## Usage
The package provides a convenient `sdg` command for common tasks.

You can check if your `.sdg` file is syntactically and semantically correct, using the command:

```bash
sdg validate examples/dataset.sdg
```

To generate the Python generator class from your DSL description, you can use the command:

```bash
sdg generate datasetname.sdg
```
By default, this creates `datasetname.py` in the current directory.
You can specify a custom output file as:

```bash
sdg generate datasetname.sdg -o my_generator.py
```

Alternatively, since the language is registered with textX, you can use standard textX commands.
Upon verifying that `sdg` is registered (using `textx list-languages` and `textx list-generators`),
you can use the registered `sdg_gen` generator (e.g. `textx generate datasetname.sdg --target sdg_gen`).

## 📂 Examples

Check the `examples/` directory for sample `.sdg` files (short description):

- `agrawal0datadescriptor.sdg` — classification generator with threshold-based rules.
- `friedmandatadescriptor.sdg` — nonlinear regression generator using sinusoidal interactions.
- `friedmandriftdescriptor.sdg` — Friedman regression with multiple concept drifts.
- `loandatadescriptor.sdg` — loan approval rules with financial thresholds.
- `mixeddatadescriptor.sdg` — mixed boolean/numeric data with abrupt drift.
- `mvdatadescriptor.sdg` — multivariate dataset with conditional dependencies.
- `staggerdatadescriptor.sdg` — boolean stagger concept (size/shape/color).

## Semantic specification
See file `OPERATIONAL_SEMANTICS.md` for the formal semantics of the DSL, 
including syntax overview, evaluation model, and logic formalization.
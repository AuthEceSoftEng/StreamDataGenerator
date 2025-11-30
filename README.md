# 🚀 Stream Data Generator DSL

A formal **Domain-Specific Language (DSL)** for describing stream dataset generators, built using the [textX](https://textx.github.io/textX/) framework.

This DSL provides a clean, structured, and type-safe way to define data streams, features, concept drift, and generation logic, replacing verbose YAML configurations.

---

## 📋 Table of Contents

- [🚀 Stream Data Generator DSL](#-stream-data-generator-dsl)
  - [📋 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [🛠️ Installation](#️-installation)
  - [📝 DSL Syntax](#-dsl-syntax)
    - [Example](#example)
    - [Language Constructs](#language-constructs)
      - [Dataset](#dataset)
      - [Parameters](#parameters)
      - [Features](#features)
      - [Target](#target)
      - [Drift](#drift)
      - [Run Configuration](#run-configuration)
    - [Supported Functions](#supported-functions)
  - [💻 Usage](#-usage)
    - [Using the `sdg` CLI](#using-the-sdg-cli)
      - [✅ 1. Validate a DSL file](#-1-validate-a-dsl-file)
      - [⚙️ 2. Generate Python Code](#️-2-generate-python-code)
      - [🔄 3. Convert YAML to DSL](#-3-convert-yaml-to-dsl)
    - [Using the `textx` CLI](#using-the-textx-cli)
      - [📜 List Registered Languages and Generators](#-list-registered-languages-and-generators)
      - [🏭 Generate Code](#-generate-code)
  - [📂 Examples](#-examples)

---

## ✨ Features

- **Formal Grammar**: Robust syntax validation and error reporting.
- **Concise Syntax**: Write less code to describe complex datasets compared to YAML.
- **Type Safety**: Built-in validation for parameter types and formulas.
- **Code Generation**: Automatically generate Python code for data generation.
- **Tooling Support**: Integrated with the textX ecosystem (CLI, visualization).
- **Drift Support**: Native syntax for defining concept drift and formula variations.

---

## 🛠️ Installation

Clone the repository and install the package in **editable mode**. This ensures all dependencies (including `textX` and `jinja2`) are installed correctly.

```bash
pip install -e .
```

> **Note**: This installation includes the `textX[cli]` extras, enabling the standard `textx` command-line tools.

---

## 📝 DSL Syntax

The DSL is designed to be readable and expressive. Blocks are terminated with the `end` keyword.

### Example

```text
dataset Agrawal0DataGenerator
    description: "Stream generator introduced by Agrawal et al."
    
    parameters
        seed: "The seed of the random generator"
    end
    
    features
        salary: UniformFloat(20000, 150000), "Salary"
        age: UniformInteger(20, 80), "Age"
        commission: 0 if salary < 75000 else UniformFloat(10000, 75000), "Commission"
    end
    
    target loanapproval:Binary
        description: "Loan Approval"
        formula: age < 40 or 60 <= age
        drift changeformula
            value: age < 40 or 60 <= age
            value: (age < 40 and salary >= 50000) or (age >= 60)
        end
    end
    
    run seed=42
end
```

### Language Constructs

#### Dataset
The top-level container for your generator definition.
```text
dataset MyGenerator
    ...
end
```

#### Parameters
Define input arguments that can be passed to the generator at runtime.
```text
parameters
    seed: "Random seed"
    noise: "Noise level"
end
```

#### Features
Define the input features (attributes) of the data stream. Each feature has a name, a generation formula, and a description.
```text
features
    age: UniformInteger(18, 90), "User Age"
    income: Gaussian(50000, 10000), "Annual Income"
end
```

#### Target
Define the target variable (label) for supervised learning tasks. You must specify the type (`Binary`, `Float`, `Integer`, `Categorical`).
```text
target churn:Binary
    description: "Customer Churn"
    formula: age > 60 and income < 30000
end
```

#### Drift
Define concept drift by specifying alternative formulas for a feature or target.
```text
drift my_drift
    value: original_formula
    value: new_formula_after_drift
end
```

#### Run Configuration
Specify default values for parameters when running the generator.
```text
run seed=42, noise=0.1
```

### Supported Functions

- `UniformFloat(min, max)`
- `UniformInteger(min, max)`
- `Gaussian(mu, sigma)`
- `UniformCategorical("val1", "val2", ...)`

---

## 💻 Usage

You can interact with the DSL using either the dedicated `sdg` CLI or the standard `textx` CLI.

### Using the `sdg` CLI

The package provides a convenient `sdg` command for common tasks.

#### ✅ 1. Validate a DSL file

Check if your `.sdg` file is syntactically and semantically correct.

```bash
sdg validate examples/dataset.sdg
```

#### ⚙️ 2. Generate Python Code

Generate the Python generator class from your DSL description.

```bash
sdg generate examples/dataset.sdg
```
*By default, this creates `datasetname.py` in the current directory.*

You can specify a custom output file:

```bash
sdg generate examples/dataset.sdg -o my_generator.py
```

#### 🔄 3. Convert YAML to DSL

Migrate your existing YAML descriptors to the new DSL format.

```bash
sdg convert-yaml examples/dataset.yml -o examples/dataset.sdg
```

### Using the `textx` CLI

Since the language is registered with textX, you can use standard textX commands.

#### 📜 List Registered Languages and Generators

Verify that `sdg` is registered.

```bash
textx list-languages
textx list-generators
```

#### 🏭 Generate Code

Use the registered `sdg_gen` generator.

```bash
textx generate examples/dataset.sdg --target sdg_gen
```

---

## 📂 Examples

Check the `examples/` directory for sample `.sdg` files:

- `agrawal0datadescriptor.sdg`
- `friedmandatadescriptor.sdg`
- `loandatadescriptor.sdg`

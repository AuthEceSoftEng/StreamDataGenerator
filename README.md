# textX DSL for StreamDataGenerator

This directory contains a formal Domain-Specific Language (DSL) for describing dataset generators, built using the textX framework.

## Overview

The DSL provides a cleaner, more structured alternative to the YAML-based dataset descriptors. It offers:
- **Formal grammar** with syntax validation
- **Better tooling** support (IDE integration, syntax highlighting)
- **Type safety** through grammar rules
- **Cleaner syntax** that's more concise than YAML

## Grammar File

- [`dataset.tx`](dataset.tx) - The textX grammar definition

## Installation

Install the package in editable mode:

```bash
pip install -e .
```

## CLI Usage

The package provides a `sdg` command-line interface.

### Validate a DSL file

```bash
sdg validate examples/dataset.sdg
```

### Generate Python Code

```bash
sdg generate examples/dataset.sdg -o output_generator.py
```

### Convert YAML to DSL

```bash
sdg convert-yaml examples/dataset.yml -o examples/dataset.sdg
```

## TextX CLI Integration

The DSL and generator are registered with textX, so you can also use the standard `textx` command.

### List Registered Languages and Generators

```bash
textx list-languages
textx list-generators
```

### Generate Code using TextX

```bash
textx generate examples/dataset.sdg --target sdg_gen
```

## DSL Syntax Example

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

## Language Constructs

### Dataset
Top-level container defining the entire dataset generator. Blocks are terminated with `end`.

### Parameters
Input parameters for the generator.
Syntax: `name: "Description"`

### Features
Data features.
Syntax: `name: formula, "Description"`

### Target
The target variable.
Syntax:
```text
target name:Type
    description: "Description"
    formula: ...
end
```

### Drift
Concept or data drift definitions with multiple formula variants.

### Distribution Functions
Supported in formulas:
- `UniformFloat(min, max)`
- `UniformInteger(min, max)`
- `Gaussian(mu, sigma)`
- `UniformCategorical("val1", "val2", ...)`

## Installation

To use the DSL parser, install textX and regex:

```bash
pip install textX regex
```

## Examples

See the `sdg/examples/` directory for converted `.sdg` files.

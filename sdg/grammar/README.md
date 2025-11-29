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

## Usage

### Parsing DSL Files

```python
from sdg.tools.dsl_parser import parse_file

# Parse a .sdg file
model = parse_file('examples/dataset.sdg')

# Access model properties
print(model.name)
print(model.features)
print(model.target)
```

### Converting YAML to DSL

```bash
python sdg/tools/convert_yaml.py sdg/examples/agrawal0datadescriptor.yml > output.sdg
```

### Testing/Validating DSL Files

```bash
python sdg/tools/test_dsl.py sdg/examples/agrawal0.sdg
```

## DSL Syntax Example

```
Dataset Agrawal0DataGenerator {
    description: "Stream generator introduced by Agrawal et al."
    
    parameters {
        seed: "The seed of the random generator"
    }
    
    features {
        salary: "Salary" = UniformFloat(20000, 150000)
        age: "Age" = UniformInteger(20, 80)
        commission: "Commission" = 0 if salary < 75000 else UniformFloat(10000, 75000)
    }
    
    target loanapproval: "Loan Approval" {
        type: Binary
        formula: age < 40 or 60 <= age
        drift changeformula {
            value: age < 40 or 60 <= age
            value: (age < 40 and salary >= 50000) or (age >= 60)
        }
    }
    
    run {
        seed = 42
    }
}
```

## Language Constructs

### Dataset
Top-level container defining the entire dataset generator.

### Parameters
Input parameters for the generator (typically just the random `seed`).

### Features
Data features with:
- Name and description
- Formula (using distribution functions or expressions)
- Optional drift specifications

### Target
The target variable with:
- Name and description
- Type (`Binary` or `Scalar`)
- Formula
- Optional drift specifications

### Drift
Concept or data drift definitions with multiple formula variants.

### Distribution Functions
- `UniformFloat(min, max)` - Uniform float distribution
- `UniformInteger(min, max)` - Uniform integer distribution
- `Gaussian(mu, sigma)` - Gaussian distribution
- `UniformCategorical(values...)` - Categorical distribution

## Installation

To use the DSL parser, install textX:

```bash
pip install textX
```

## Examples

See the `examples/` directory for converted `.sdg` files from all YAML examples.

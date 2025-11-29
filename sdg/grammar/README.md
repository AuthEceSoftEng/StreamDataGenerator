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

---
layout: page
title: DSL Reference
permalink: /dsl/
nav_order: 3
---

The SDG DSL is built on [textX](https://textx.github.io/textX/). Every `.sdg` file describes a single **dataset generator** whose grammar is validated before any code is produced.

---

## Top-Level Structure

```text
dataset <Name>
    [description: "<text>"]
    [parameters ... end_parameters]
    [features   ... end_features]
    [target     ... end_target]
    [drifts     ... end_drifts]
end_dataset
```

All blocks are optional but must appear in the order shown when present.

---

## Parameters

Runtime arguments that can be referenced inside feature or target formulas.

```text
parameters
    seed:  "Random seed for reproducibility"
    noise: "Noise level"
end_parameters
```

---

## Features

The input columns of each generated instance.

```text
features
    <type> <name>: <formula> [, "<description>"]
    ...
end_features
```

### Supported types

| Type | Python equivalent |
|------|------------------|
| `int` | `int` |
| `float` | `float` |
| `string` | `str` |
| `bool` | `bool` |

### Supported distribution functions

| Function | Description |
|----------|-------------|
| `UniformFloat(min, max)` | Continuous uniform float in `[min, max]` |
| `UniformInteger(min, max)` | Discrete uniform integer in `[min, max]` |
| `Gaussian(mu, sigma)` | Normal distribution with mean `mu` and std `sigma` |
| `UniformCategorical("v1", "v2", ...)` | Uniform random choice among the listed strings |

Formulas may also be arbitrary Python-compatible expressions referencing `parameters` and **previously declared** features (in declaration order).

### Example

```text
features
    int    age:    UniformInteger(18, 90),           "User age"
    float  income: Gaussian(50000, 10000),           "Annual income"
    string status: UniformCategorical("active", "inactive"), "Account status"
    bool   senior: age > 60,                         "Senior flag"
end_features
```

---

## Target

The label for supervised learning tasks.

```text
target <name>: <ClassType>
    description: "<text>"
    formula: <python-expression>
end_target
```

### Class types

| Type | Behaviour |
|------|-----------|
| `Binary` | `1` if formula is truthy, else `0` |
| `Categorical` | raw formula value (string or int) |
| `Scalar` | raw formula value (numeric) |

### Example

```text
target churn: Binary
    description: "Customer churn"
    formula: age > 60 and income < 30000
end_target
```

---

## Drifts

Drifts alter the distribution of a feature (or the target formula) after a certain point in the stream.

```text
drifts
    drift on <variable>
        type: <drift_type> [, <drift_type> ...]
        scenarios
            <formula> [,
            <formula> ...]
        end_scenarios
    end_drift
    ...
end_drifts
```

### Drift types

| Type | Description |
|------|-------------|
| `sudden` | The new scenario replaces the old immediately |
| `gradual` | Old and new coexist probabilistically during a transition window |
| `incremental` | Linear interpolation between old and new over a fixed number of steps |
| `recurring` | The alternative scenario reappears periodically |

### Scenario semantics

- Scenario 0 is always the **default** formula (the one in the `features` block).
- Additional scenarios in the `scenarios` block are activated by the drift machinery.
- A single formula is valid (i.e. the list may have length 1).

### Example

```text
drifts
    drift on salary
        type: sudden
        scenarios
            UniformFloat(10000, 40000),
            UniformFloat(30000, 80000)
        end_scenarios
    end_drift
end_drifts
```

---

## CLI Commands

### Validate

Check syntax and semantics without generating code:

```bash
sdg validate <file.sdg>
```

### Generate

Produce a Python generator class:

```bash
sdg generate <file.sdg>                   # outputs <file>.py
sdg generate <file.sdg> -o my_gen.py      # custom output path
```

The generated class exposes a `generate(n)` method that returns a list of `n` instances, each a dict of `{feature: value, ..., target: value}`.

### textX equivalents

```bash
textx generate <file.sdg> --target sdg_gen    # Python class
textx generate <file.sdg> --target sdg_docs   # documentation artefact
```

---

## Formal Semantics

For the full operational semantics (abstract syntax, evaluation model, state transitions, and constraints) see [`OPERATIONAL_SEMANTICS.md`](https://github.com/AuthEceSoftEng/StreamDataGenerator/blob/main/OPERATIONAL_SEMANTICS.md) in the repository.

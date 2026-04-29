---
layout: home
title: Home
nav_order: 1
---

**A formal Domain-Specific Language for describing stream dataset generators, with LLM-assisted authoring.**

SDG (Stream Data Generator DSL) lets you define data streams — including features, a target variable, and concept/data drifts — in a concise, validated syntax. From a single `.sdg` file the tool generates a ready-to-use Python class. Natural language descriptions can also be turned into `.sdg` files automatically via an LLM.

[GitHub Repository](https://github.com/AuthEceSoftEng/StreamDataGenerator){: .btn .btn-primary }

---

## What SDG Does

| Step | What happens |
|------|-------------|
| ✍️ **Describe** | Write a `.sdg` file (or provide a plain-text description) |
| ✅ **Validate** | Grammar and semantic checks catch errors before generation |
| ⚙️ **Generate** | `sdg generate` produces a Python generator class |
| 🤖 **LLM assist** | `generate_sdg.py` turns a text description into a `.sdg` file |
| 🌊 **Stream** | The generated class produces instances with optional drift behaviour |

---

## Quick Start

```bash
git clone https://github.com/AuthEceSoftEng/StreamDataGenerator.git
cd StreamDataGenerator
pip install -e .
```

Validate and generate from an example:

```bash
sdg validate examples/loandatadescriptor.sdg
sdg generate examples/loandatadescriptor.sdg
```

Generate a `.sdg` file from a plain-text description (requires an LLM API key):

```bash
python generate_sdg.py examples_nl_descriptions/onlineretail.txt
```

---

## Minimal Example

```text
dataset LoanDataGenerator

    parameters
        seed: "The seed of the random generator"
    end_parameters

    features
        float salary: UniformFloat(20000, 150000), "Salary of the applicant"
        int age:      UniformInteger(20, 80),       "Age of the applicant"
    end_features

    target loanapproval: Binary
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

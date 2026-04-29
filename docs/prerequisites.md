---
layout: page
title: Prerequisites & Installation
permalink: /prerequisites/
nav_order: 2
---

## Requirements

- **Python 3.9+**
- **pip**
- For LLM-assisted `.sdg` generation: an API key for at least one supported provider (see the [LLM Guide](/llm/)), **or** [Ollama](https://ollama.ai) installed locally for fully offline use

---

## Installation

```bash
git clone https://github.com/AuthEceSoftEng/StreamDataGenerator.git
cd StreamDataGenerator
pip install -e .
```

Installing in editable mode (`-e`) registers the `sdg` CLI command and the textX language/generator extensions automatically.

---

## Verify the Installation

```bash
sdg --help
textx list-languages    # should list: sdg
textx list-generators   # should list: sdg_gen, sdg_docs
```

---

## Examples

The `examples/` directory contains ready-to-use `.sdg` files:

| File | Description |
|------|-------------|
| `agrawal0datadescriptor.sdg` | Classification generator with threshold-based rules |
| `friedmandatadescriptor.sdg` | Nonlinear regression using sinusoidal interactions |
| `friedmandriftdescriptor.sdg` | Friedman regression with multiple concept drifts |
| `loandatadescriptor.sdg` | Loan approval with financial thresholds |
| `mixeddatadescriptor.sdg` | Mixed boolean/numeric data with abrupt drift |
| `mvdatadescriptor.sdg` | Multivariate dataset with conditional dependencies |
| `staggerdatadescriptor.sdg` | Boolean stagger concept (size/shape/color) |

Natural language description examples are in `examples_nl_descriptions/`.

---

## Running the Examples

```bash
# validate
sdg validate examples/loandatadescriptor.sdg

# generate Python class
sdg generate examples/loandatadescriptor.sdg

# run all examples and inspect output
python run_examples.py
python run_nl_examples.py
```

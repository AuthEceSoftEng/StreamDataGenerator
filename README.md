# StreamDataGenerator
Generator that creates data stream generators.

## Usage
First, install all required libraries using `pip install -r requirements.txt`  
After that, run the following command to generate code for a dataset generator:

```
python dataset_generator.py --input input.yaml --output output.py --strict --gendoc
```

The input is a YAML descriptor file and the output is a data stream generator as a Python file.  
The documentation page of the data stream generator can also be generated using the `--gendoc` option.  
Also, using the `--strict` option instructs the generator to treat all warnings as errors.

## Input format
YAML descriptor file that is given as input must have the following format:

```yaml

dataset:
  name: {{the name of the dataset generator}}
  description: {{the description of the dataset generator, can be multi-line}}
  imports: {{any required imports, e.g. math}}
  parameters:
    - name: seed
      description: The seed of the random generator
    - name: {{any required parameter}}
      description: {{parameter description}}
    - ...
  features:
    - name: {{the name of the first feature}}
      description: {{description of the feature}}
      formula: {{formula of the feature}}
      drift:
        type: changeformula
        formulas:
          - name: {{optional name of this data drift choice}}
            value: {{formula of data drift choice}}
          - ...
    - name: {{the name of the second feature}}
      description: {{description of the feature}}
      formula: {{formula of the feature}}
    - ...
  target:
    name: {{the name of the target variable}}
    description: {{description of the target variable}}
    classtype: {{type of the target, one of Binary, Categorical, Scalar}}
    formula: {{formula of the target cariable}}
    drift:
      type: changeformula
      formulas:
        - name: {{optional name of this first concept drift choice}}
          value: {{formula of concept drift choice}}
        - name: {{optional name of this second concept drift choice}}
          value: {{formula of concept drift choice}}
        - ...
```

Formulas can be written in standard Python code and refer to other variables. Moreover, they can include the functions:  
- `UniformInteger(a, b)`: returns a random integer, uniformly distributed in range [a, b]
- `UniformFloat(a, b)`: returns a random float, uniformly distributed in range [a, b]
- `Gaussian(mu, sigma)`: returns a random float from a Gaussian distribution with parameters mu and sigma
- `UniformCategorical(cat1, cat2, cat3, ...)`: returns one of the categories cat1, cat2, cat3, ... at random (uniformly)

Examples of descriptor files can be found in folder [sdg/examples](sdg/examples).

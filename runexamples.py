import os
import yaml
from sdg.generator.codegenerator import generate, generate_run
from sdg.generator.documentationgenerator import generate_doc

if __name__ == '__main__':
    for filename in os.listdir(os.path.join("sdg", "examples")):
        if filename.endswith("yml"):
            print("Running input file " + filename)
            datasetname = filename[:-18]
            inputfilename = os.path.join("sdg", "examples", filename)
            outputfilename = inputfilename[:-18] + "datagenerator.py"
            # Read yaml descriptor
            with open(inputfilename) as infile:
                yamlinput = yaml.safe_load(infile)["dataset"]
            # Generate output code
            with open(outputfilename, 'w') as outfile:
                outfile.write(generate(yamlinput) + generate_run(yamlinput))
            # Generate also documentation
            with open(outputfilename[:-2] + "html", 'w') as outfile:
                outfile.write(generate_doc(outputfilename))
            print(" Done!")

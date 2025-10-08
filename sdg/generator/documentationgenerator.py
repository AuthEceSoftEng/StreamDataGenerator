import re
import sys
import inspect
import importlib
from pydoc import HTMLDoc

def load_class_from_path(path):
    spec = importlib.util.spec_from_file_location("mymodule", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["mymodule"] = module
    spec.loader.exec_module(module)
    return [obj for _, obj in inspect.getmembers(module) if inspect.isclass(obj)][0]

def generate_doc(filename):
    DataGenerator = load_class_from_path(filename)
    docgen = HTMLDoc()
    htmldoc = docgen.document(DataGenerator)
    htmldoc = re.sub(r"<td colspan=2><tt>[^<]+<br>", "<td colspan=2><tt>", htmldoc)
    htmldoc = re.sub(r"\(<a href=\"builtins.html#object\">builtins.object</a>\)", "", htmldoc)
    htmldoc = re.sub(r":param[^;]+;[^:]+:", r"<b>Parameter</b>&nbsp;s1:", htmldoc)
    htmldoc = re.sub(r":returns:", r"<b>Returns:</b>", htmldoc)
    htmldoc = htmldoc.replace("<tr><td>&nbsp;</td>\n<td width=\"100%\">Methods defined here:<br>", "<td bgcolor=\"#ffc8d8\" width=\"100%\"><b>Methods:</b>")
    htmldoc = htmldoc[:htmldoc.find("<hr>\nData descriptors defined here:")] + "</td></tr><tr bgcolor=\"#ffc8d8\"><td colspan=\"3\">&nbsp;</td></tr></table>"
    htmldoc = htmldoc.replace("#ffc8d8", "#fcdce5")
    return htmldoc

if __name__ == "__main__":
    datasetname = "stagger"
    codefilename = "../examples/" + datasetname + "datagenerator.py"    
    outputfilename = codefilename[:-2] + "html"
    
    dochtml = generate_doc(codefilename)
    with open(outputfilename, "w") as f:
        f.write(dochtml)    

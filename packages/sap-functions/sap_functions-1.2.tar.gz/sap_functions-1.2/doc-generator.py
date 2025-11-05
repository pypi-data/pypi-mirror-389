import os
import inspect
import importlib
import pkgutil
from pathlib import Path



def generate_md_doc_for_codebase(module_name: str, output_file="README.md"):
    """Generate a single Markdown documentation file for all classes and functions in a package."""
    docs = [f"""
# sap_functions
Library with utility classes and functions to facilitate the development of SAP automations in python.

This module is built on top of SAP Scripting and aims to making the development of automated workflows easier and quicker.

## Implementation example
```python
from sap_functions import SAP

sap = SAP()
sap.select_transaction("COOIS")
```
This script:

Checks for existant SAP GUI instances.
Connects to that instance.
Write "COOIS" in the transaction field.
# Classes overview"""]
    package = importlib.import_module(module_name)

    for _, submodule_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            submodule = importlib.import_module(submodule_name)
        except Exception as e:
            print(f"Skipping {submodule_name}: {e}")
            continue

        docs.append(f"\n## Module `{submodule_name}`\n")

        classes = inspect.getmembers(submodule, inspect.isclass)
        classes = [class_ for class_ in classes if class_[1].__module__ == submodule_name]
        class_docs = []

        for class_name, cls in classes:
            if not cls.__module__.startswith(module_name):
                continue

            class_header = f"### Class `{class_name}` \n"
        
            class_docs.append(class_header)

            attrs = [
                a for a in vars(cls)
                if not callable(getattr(cls, a)) and not a.startswith("__")
            ]
            if attrs:
                class_docs.append("**Attributes:**")
                for attr in attrs:
                    class_docs.append(f"- `{attr}`")
                class_docs.append("")

            methods = inspect.getmembers(cls, predicate=inspect.isfunction)
            if methods:
                class_docs.append("**Methods:**")
                for _, method in methods:
                    class_docs.append(_format_function_doc(method))
                class_docs.append("")
        
        if class_docs:
            docs.extend(class_docs)

        functions = inspect.getmembers(submodule, inspect.isfunction)
        func_docs = []
        for _, func in functions:
            if func.__module__.startswith(module_name):
                func_docs.append(_format_function_doc(func))

        if func_docs and len(class_docs)==0:
            docs.append("### Top-level Functions\n")
            docs.extend(func_docs)
            docs.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(docs))

    print(f"Documentation saved to `{output_file}`")


def _format_function_doc(func):
    """Format a function or method signature into Markdown."""
    sig = inspect.signature(func)
    params = []

    for param_name, param in sig.parameters.items():
        prefix = ""
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            prefix = "*"
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            prefix = "**"

        param_str = f"{prefix}{param_name}"

        if param.annotation != inspect._empty:
            ann = param.annotation
            ann_str = ann.__name__ if hasattr(ann, "__name__") else str(ann)
            param_str += f": {ann_str}"

        if param.default != inspect._empty:
            param_str += f" = {repr(param.default)}"

        params.append(param_str)

    params_str = ", ".join(params)
    ret_str = ""
    if sig.return_annotation != inspect._empty:
        ann = sig.return_annotation
        ret_str = f" -> {ann.__name__ if hasattr(ann, '__name__') else ann}"

    doc = inspect.getdoc(func)
    short_doc = doc.split("\n")[0] if doc else ""
    return f"- `{func.__name__}({params_str}){ret_str}`: {short_doc}"


if __name__ == "__main__":
    import sys
    sys.path.append("src")
    generate_md_doc_for_codebase("sap_functions")
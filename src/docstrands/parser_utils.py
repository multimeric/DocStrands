"""
Utility functions that apply to docstring_parser types
"""
from docstring_parser import Docstring, DocstringParam


def find_param(doc: Docstring, param_name: str) -> int | None:
    """
    Returns the index of the parameter with the given name, or None if it does not exist
    """
    for i, param in enumerate(doc.params):
        if param_name == param.arg_name:
            return i
    return None

def get_param(doc: Docstring, param_name: str) -> DocstringParam | None:
    """
    Returns an existing parameter definition
    """
    i = find_param(doc, param_name)
    return doc.params[i] if i is not None else None

def delete_param(doc: Docstring, param_name: str):
    """
    Deletes any parameters with the given name
    """
    doc.meta = [meta for meta in doc.meta if not (isinstance(meta, DocstringParam) and meta.arg_name == param_name)]

def add_param(doc: Docstring, param: DocstringParam):
    """
    Adds a parameter to the docstring.
    If an existing parameter with the same name exists, it replaces it in the same position
    """
    i = find_param(doc, param.arg_name)
    if i is not None:
        doc.params[i] = param
    else:
        doc.params.append(param)
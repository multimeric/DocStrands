from abc import ABC, abstractmethod
from io import StringIO
from pydoc import Helper

import docstring_parser
from docstrands import DocstringStyle, STYLE_MAP
import pytest
import griffe

GRIFFE_STYLE_MAP: dict[DocstringStyle, griffe.DocstringStyle] = {
    "google": "google",
    "numpydoc": "numpy",
    "rest": "sphinx"
}

class DocstringTester(ABC):
    style: DocstringStyle

    def __init__(self, obj: object, style: DocstringStyle) -> None:
        self.style = style

    @abstractmethod
    def has_parameter(self, name: str, description: str | None = None) -> bool:
        pass

class StringTesterMixin:
    doc: str

    def has_parameter(self, name: str, description: str | None = None) -> bool:
        if description is None:
            return f"{name}:" in self.doc
        else:
            return f"{name}: {description}" in self.doc

class DocTester(StringTesterMixin, DocstringTester):
    """
    Tests docstrings directly via the __doc__ attribute.
    """
    def __init__(self, obj: object, style: DocstringStyle) -> None:
        if obj.__doc__ is None:
            raise ValueError("Object has no docstring.")
        self.doc = obj.__doc__
        super().__init__(obj, style)


class HelpTester(StringTesterMixin, DocstringTester):
    """
    Tests docstrings via the built-in help() function.
    """
    def __init__(self, obj: object, style: DocstringStyle) -> None:
        output = StringIO()
        helper = Helper(output=output)
        helper(obj)
        self.doc = output.getvalue()
        super().__init__(obj, style)

class DocstringParserTester(DocstringTester):
    """
    Tests docstrings via the docstring_parser module.
    """
    doc: docstring_parser.Docstring

    def __init__(self, obj: object, style: DocstringStyle) -> None:
        self.doc = docstring_parser.parse_from_object(obj, style=STYLE_MAP[style])
        super().__init__(obj, style)

    def has_parameter(self, name: str, description: str | None = None) -> bool:
        for param in self.doc.params:
            if param.arg_name == name:
                if description is None:
                    return True
                else:
                    return param.description == description
        return False

class GriffeTester(DocstringTester):
    """
    Uses the Griffe library to parse and test docstrings
    """
    doc: griffe.Docstring

    def __init__(self, obj: object, style: DocstringStyle):
        if obj.__doc__ is None:
            raise ValueError("Object has no docstring.")
        self.doc = griffe.Docstring(obj.__doc__, parser=GRIFFE_STYLE_MAP[style])
        super().__init__(obj, style)

    def has_parameter(self, name: str, description: str | None = None) -> bool:
        for section in self.doc.parsed:
            if isinstance(section, griffe.DocstringSectionParameters):
                for param in section.value:
                    if param.name == name:
                        if description is None:
                            return True
                        else:
                            return param.description == description
        return False

each_tester = pytest.mark.parametrize("Tester", [DocTester, HelpTester, DocstringParserTester, GriffeTester])
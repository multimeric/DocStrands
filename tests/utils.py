from __future__ import annotations
from abc import ABC, abstractmethod
from io import StringIO
from pydoc import Helper
import re

import docstring_parser
from docstrands.parsed_func import DocstringStyle, STYLE_MAP
import pytest
import griffe

GRIFFE_STYLE_MAP: dict[DocstringStyle, griffe.DocstringStyle] = {
    "google": "google",
    "numpydoc": "numpy",
    "rest": "sphinx",
}


def strip_whitespace(string: str) -> str:
    return string.replace("\n", "").replace(" ", "")


class DocstringTester(ABC):
    style: DocstringStyle

    def __init__(self, obj: object, style: DocstringStyle) -> None:
        self.style = style

    @abstractmethod
    def has_parameter(
        self, name: str, description: str | None = None, type: str | None = None
    ) -> bool:
        """
        Checks if the docstring has a parameter with the given name and (optionally) description and type.
        """
        pass

    @abstractmethod
    def has_returns(self, returns: str, type: str | None = None) -> bool:
        """
        Checks if the docstring has a return value with the given description.
        """
        pass

    @abstractmethod
    def has_synopsis(self, synopsis: str) -> bool:
        """
        Checks if the docstring has a given synopsis.
        """
        pass

    @abstractmethod
    def has_description(self, description: str) -> bool:
        """
        Checks if the docstring has a given description.
        """
        pass


class StringTesterMixin:
    # Note: currently assumes that all docstrings are Google style
    doc: str

    def _doc_bounded_contains(self, text: str) -> bool:
        """
        Checks if a given string is contained within the docstring, with \\b boundary delimiters
        """
        return re.search(f"\\b{text}\\b", self.doc) is not None

    def has_parameter(
        self, name: str, description: str | None = None, type: str | None = None
    ) -> bool:
        # These tests are a bit loose, but the other tester subclasses do a more precise job
        if description is not None and description not in self.doc:
            # Missing param description
            return False
        if type is not None and type not in self.doc:
            # Missing type description
            return False
        # Only use the word boundary test for the parameter name, since e.g. `"a" in self.doc` is very likely to return True
        return self._doc_bounded_contains(name)

    def has_returns(self, returns: str, type: str | None = None) -> bool:
        return (
            "Returns" in self.doc
            and returns in self.doc
            and (type is None or type in self.doc)
        )

    def has_synopsis(self, synopsis: str) -> bool:
        return synopsis in self.doc

    def has_description(self, description: str) -> bool:
        # We need to split the description into lines because the pydoc help system
        # adds indentation
        for line in description.split("\n"):
            if line not in self.doc:
                return False
        return True


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

    def has_parameter(
        self, name: str, description: str | None = None, type: str | None = None
    ) -> bool:
        for param in self.doc.params:
            if param.arg_name == name:
                return all(
                    [
                        description is None or param.description == description,
                        type is None or param.type_name == type,
                    ]
                )
        return False

    def has_returns(self, returns: str, type: str | None = None) -> bool:
        return (
            self.doc.returns is not None
            and self.doc.returns.description is not None
            and returns in self.doc.returns.description
            and (type is None or self.doc.returns.type_name == type)
        )

    def has_synopsis(self, synopsis: str) -> bool:
        return self.doc.short_description == synopsis

    def has_description(self, description: str) -> bool:
        return self.doc.long_description == description


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

    def has_parameter(
        self, name: str, description: str | None = None, type: str | None = None
    ) -> bool:
        for section in self.doc.parsed:
            if isinstance(section, griffe.DocstringSectionParameters):
                for param in section.value:
                    if param.name == name:
                        return all(
                            [
                                description is None or param.description == description,
                                type is None or param.annotation == type,
                            ]
                        )
        return False

    def has_returns(self, returns: str, type: str | None = None) -> bool:
        for section in self.doc.parsed:
            if isinstance(section, griffe.DocstringSectionReturns):
                for line in section.value:
                    return line.description == returns and (
                        type is None or line.value == type
                    )
        return False

    def has_synopsis(self, synopsis: str) -> bool:
        for section in self.doc.parsed:
            if isinstance(section, griffe.DocstringSectionText):
                # Griffe does not separate the synopsis from the description
                return synopsis in section.value
        return False

    def has_description(self, description: str) -> bool:
        for section in self.doc.parsed:
            if isinstance(section, griffe.DocstringSectionText):
                return description in section.value
        return False


each_tester = pytest.mark.parametrize(
    "Tester", [DocTester, HelpTester, DocstringParserTester, GriffeTester]
)

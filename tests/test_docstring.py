from io import StringIO
from typing import Type
from docstrands import docstring
from pydoc import render_doc, Helper
import pytest
from utils import each_tester, DocTester

@pytest.fixture
def help() -> Helper:
    """
    Exactly the same as the built-in help() function, but captures the output for testing.
    """
    return Helper(output=StringIO())

@pytest.fixture
def help_output(help: Helper) -> StringIO:
    """
    Returns the output of the help() function.
    """
    assert isinstance(help.output, StringIO)
    return help.output


@docstring(style="google")
def divide(a: int, b: int, *, floor: bool) -> float:
    """Divide two numbers.

    Args:
        a: The dividend.
        b: The divisor.
        floor: Whether to use  the result.

    Returns:
        The result of the division.
    """
    return a // b if floor else a / b

@docstring(style="google")
def source(a: int, b: int, *, c: bool) -> None:
    """
    Some description

    Args:
        a: Positional argument a
        b: Positional argument b
        c: Keyword-only argument c

    Returns:
        Result
    """

@source.copy_params("a", "b")
@docstring(style="google")
def param_dest(a: int, b: int, d: float):
    """
    Some new description

    Args:
        d: A unique parameter
    """
    pass

@source.copy_params("a", "b")
@docstring(style="google")
def return_dest(a: int, b: int):
    pass

@each_tester
def test_docstring(Tester: Type[DocTester]):
    tester = Tester(param_dest, "google")
    assert tester.has_parameter("a", "Positional argument a")
    assert tester.has_parameter("b", "Positional argument b")
    assert not tester.has_parameter("c")
    assert tester.has_parameter("d", "A unique parameter")
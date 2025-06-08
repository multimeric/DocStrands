from typing import Annotated
from docstrands.parsed_func import extract_typename
from docstrands import Description, TypeDescription
from tests.utils import at_least_310

@at_least_310
def test_extract_typename():
    assert extract_typename(float) == "float"
    assert extract_typename(None) == "None"
    assert extract_typename(str | int) == "str | int"
    assert extract_typename(Annotated[int, "foo"]) == "int"
    assert extract_typename(Annotated[int, Description("foo")]) == "int"
    assert extract_typename(Annotated[int, TypeDescription("foo")]) == "foo"

from typing import Annotated, Optional
from docstrands.signature import parse_type
from docstrands import Description, TypeDescription
from tests.utils import at_least_310

@at_least_310
def test_extract_typename():
    assert parse_type(float) == (None, "float")
    assert parse_type("float") == (None, "float")
    assert parse_type(None) == (None, "None")
    assert parse_type(str | int) == (None, "str | int")
    assert parse_type(Optional["int"]) == (None, "Optional[int]")
    assert parse_type(Annotated[int, "foo"]) == (None, "int")
    assert parse_type(Annotated[int, Description("foo")]) == ("foo", "int")
    assert parse_type(Annotated[int, TypeDescription("foo")]) == (None, "foo")

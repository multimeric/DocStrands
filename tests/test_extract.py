from docstrands.signature import parse_uneval_type
from tests.utils import at_least_310
import pytest
import ast


@at_least_310
@pytest.mark.parametrize(
    "signature, expected_descr, expected_type",
    [
        ("float", None, "float"),
        ("'float'", None, "float"),
        ("None", None, "None"),
        ("str | int", None, "str | int"),
        ("Optional[int]", None, "Optional[int]"),
        ("Annotated[int, 'foo']", None, "int"),
        ("Annotated[int, Description('foo')]", "foo", "int"),
        ("Annotated[int, TypeDescription('foo')]", None, "foo"),
    ],
)
def test_extract_typename(
    signature: str, expected_descr: str | None, expected_type: str | None
):
    """
    Test that parse_uneval_type correctly extracts the description and type from an ast.expr
    that represents a type signature.
    """
    expr = ast.parse(signature, mode="eval").body
    assert parse_uneval_type(expr) == (expected_descr, expected_type)

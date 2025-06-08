from typing import Annotated, Type
from docstrands import Description, docstring
from tests.utils import DocTester, each_tester

AnnotatedReturn = Annotated[str, Description("The return value.")]
AnnotatedParam = Annotated[int, Description("An int parameter.")]
UnionParam = Annotated[int | float, Description("An int or float parameter.")]
DoubleAnnotatedParam = Annotated[Annotated[float, Description("A float parameter.")], "foo"]

@docstring(style="google", use_annotations=True)
def add(a: AnnotatedParam, b: DoubleAnnotatedParam, c: UnionParam) -> AnnotatedReturn:
    ...

@each_tester
def test_annotations(Tester: Type[DocTester]):
    tester = Tester(add, "google")
    assert tester.has_parameter("a", "An int parameter.", "int")
    assert tester.has_parameter("b", "A float parameter.", "float")
    assert tester.has_parameter("c", "An int or float parameter.", "int | float")
    assert tester.has_returns("The return value.")
# These tests also check that actual docstrings are not needed 
# And that the docstring decorator works with annotations only
from __future__ import annotations
from typing import Annotated, Type
from docstrands import Description, docstring, TypeDescription
from tests.utils import DocTester, each_tester, at_least_310

@at_least_310
@each_tester
def test_description(Tester: Type[DocTester]):

    @docstring(style="google", use_annotations=True)
    def add(
        a: Annotated[int, Description("An int parameter.")],
        b: Annotated[Annotated[float, Description("A float parameter.")], "foo"],
        c: Annotated[int | float, Description("An int or float parameter.")],
        d: "Annotated[int | None, Description('String union.')]"
    ) -> Annotated[str, Description("The return value.")]:
        ...

    tester = Tester(add, "google")
    assert tester.has_parameter("a", "An int parameter.", "int")
    assert tester.has_parameter("b", "A float parameter.", "float")
    assert tester.has_parameter("c", "An int or float parameter.", "int | float")
    assert tester.has_parameter("d", "String union.", "int | None")
    assert tester.has_returns("The return value.")

@at_least_310
@each_tester
def test_type_description(Tester: Type[DocTester]):

    @docstring(style="google", use_annotations=True)
    def add(
        a: Annotated[int | list[int], TypeDescription("An int or list thereof.")],
    ):
        ...

    tester = Tester(add, "google")
    assert tester.has_parameter("a", "", "An int or list thereof.")

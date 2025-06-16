from typing import Annotated, Any
from docstrands.signature import docstring_from_signature
from docstrands.annotations import Description, TypeDescription


def test_signature():
    # Tests docstring_from_signature
    def example(
        a: Annotated[int, TypeDescription("integer")],
        /,
        b: Annotated[float | str, Description("This configures xyz")] = 1.0,
        *,
        c: bool = True,
        **kwargs: Any,
    ) -> Annotated[None, Description("Don't use this"), TypeDescription("nothing")]:
        pass

    doc = docstring_from_signature(example)
    assert len(doc.params) == 4
    assert doc.params[0].arg_name == "a"
    assert doc.params[0].type_name == "integer"
    assert doc.params[0].description is None
    assert doc.params[0].default is None
    assert doc.params[0].is_optional is False

    assert doc.params[1].arg_name == "b"
    assert doc.params[1].type_name == "float | str"
    assert doc.params[1].description == "This configures xyz"
    assert doc.params[1].default == "1.0"
    assert doc.params[1].is_optional is True

    assert doc.returns is not None
    assert doc.returns.args == []
    assert doc.returns.description == "Don't use this"
    assert doc.returns.type_name == "nothing"
    assert doc.returns.is_generator is False
    assert doc.returns.return_name is None

def test_no_return():
    """
    Tests that a function with no return type annotation will not get a returns section.
    """
    def example(
        a: Annotated[int, TypeDescription("integer")],
    ): pass

    doc = docstring_from_signature(example)
    assert doc.returns is None
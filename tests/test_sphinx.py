from docstrands.parsed_func import docstring

@docstring(style="rest")
def source(a: int, b: int, *, c: bool) -> None:
    """
    Some description.

    Some more detail about the function.
    This has several lines.

    :param a: Positional argument a
    :param b: Positional argument b
    :param c: Keyword-only argument c
    :returns: The result
    """

@source.copy_params("a", "b", "c")
@source.copy_returns()
@source.copy_description()
@source.copy_synopsis()
@docstring(style="rest")
def dest(a: int, b: int, *, c: bool) -> None:
    pass

def test_description():
    assert set(source.__doc__.split("\n")) == set(dest.__doc__.split("\n"))
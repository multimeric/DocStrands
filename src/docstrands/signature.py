"""
Utilities for extracting type information by inspecting functions rather than parsing docstrings.
"""

from __future__ import annotations
from itertools import zip_longest
from textwrap import dedent
from typing import Callable, Any, Iterable
from docstring_parser import Docstring, DocstringParam, DocstringReturns
import inspect
import ast

from docstrands.annotations import Description, TypeDescription


def parse_uneval_type(typ: ast.expr | None) -> tuple[str | None, str | None]:
    """
    Given an unevaluated type signature as a string, returns a tuple of (value description, type signature).
    This does not evaluate the type, meaning that Python version is not important.
    """
    if typ is None:
        return None, None

    description: str | None = None
    type_name = ast.unparse(typ)
    # Peel away any number of Annotated until we reach the inner type
    while True:
        match typ:
            case ast.Subscript(
                value=ast.Name(id="Annotated"),
                slice=ast.Tuple(elts=[typ, *annotations]),
            ):
                # Peel away the Annotated type each iteration
                type_name: str = ast.unparse(typ)
                for annotation in annotations:
                    # If we find a Description or TypeDescription, we update the return value
                    compiled = compile(
                        ast.Expression(annotation), filename="<ast>", mode="eval"
                    )
                    result = eval(compiled)
                    if isinstance(result, Description):
                        description = result.description
                    elif isinstance(result, TypeDescription):
                        type_name = result.description
            case ast.Constant(value=str()):
                # Evaluate types expressed as strings
                compiled = compile(ast.Expression(typ), filename="<ast>", mode="eval")
                result = type_name = eval(compiled)
                typ = ast.parse(result, mode="eval").body
            case _:
                return description, type_name


def iter_params_with_defaults(
    func: ast.FunctionDef,
) -> Iterable[tuple[ast.arg, ast.expr | None]]:
    """
    Iterates over the parameters of a function definition, yielding each parameter along with its default value.
    If the parameter has no default value, None is yielded.
    """
    for param in func.args.posonlyargs:
        yield param, None
    yield from zip_longest(func.args.args, func.args.defaults, fillvalue=None)  # type: ignore
    if func.args.vararg is not None:
        yield func.args.vararg, None
    yield from zip_longest(func.args.kwonlyargs, func.args.kw_defaults, fillvalue=None)  # type: ignore
    if func.args.kwarg is not None:
        yield func.args.kwarg, None


def docstring_from_signature(func: Callable[..., Any]) -> Docstring:
    """
    Builds a Docstring object based on the function's signature only.
    """
    doc = Docstring()

    parsed = ast.parse(dedent(inspect.getsource(func)), mode="exec").body[0]

    if not isinstance(parsed, ast.FunctionDef):
        raise ValueError(
            "func was not a function definition. Perhaps it was a lambda or callable object?"
        )

    for param, default in iter_params_with_defaults(parsed):
        param_description, type_name = parse_uneval_type(param.annotation)
        doc.meta.append(
            DocstringParam(
                arg_name=param.arg,
                description=param_description,
                default=ast.unparse(default) if default is not None else None,
                type_name=type_name,
                is_optional=default is not None,
                args=["param", param.arg],
            )
        )

    ret_description, ret_type = parse_uneval_type(parsed.returns)
    doc.meta.append(
        DocstringReturns(
            type_name=ret_type,
            description=ret_description,
            is_generator=inspect.isgeneratorfunction(func),
            return_name=None,
            args=[],
        )
    )

    return doc

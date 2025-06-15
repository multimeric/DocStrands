"""
Utilities for extracting type information by inspecting functions rather than parsing docstrings.
"""
from __future__ import annotations
from typing import Callable, Any
from docstring_parser import Docstring, DocstringParam, DocstringReturns
from typing import (
    Annotated,
    Callable,
    Any,
    get_args,
    get_origin,
)
from docstring_parser import (
    DocstringParam,
    Docstring,
    DocstringReturns,
)
import inspect
import ast

from docstrands.annotations import Description, TypeDescription

def extract_description(typ: str) -> str | None:
    """
    Extracts the description from a type signature provided as a string.
    """
    if get_origin(typ) is Annotated:
        for annotation in get_args(typ):
            if isinstance(annotation, Description):
                return annotation.description

def parse_uneval_type(typ: str) -> tuple[str | None, str]:
    """
    Given an unevaluated type signature as a string, returns a tuple of (value description, type signature).
    This does not evaluate the type, meaning that Python version is not important.
    """
    parsed: ast.expr = ast.parse(typ, mode="eval").body
    description: str | None = None
    type_name = typ
    # Peel away any number of Annotated until we reach the inner type
    while True:
        match parsed:
            case ast.Subscript(
                value=ast.Name(id="Annotated"),
                slice=ast.Tuple(elts=[parsed, *annotations]),
            ):
                # Peel away the Annotated type each iteration
                type_name: str = ast.unparse(parsed)
                for annotation in annotations:
                    # If we find a Description or TypeDescription, we update the return value
                    compiled = compile(ast.Expression(annotation), filename="<ast>", mode="eval")
                    result = eval(compiled)
                    if isinstance(result, Description):
                        description = result.description
                    elif isinstance(result, TypeDescription):
                        type_name = result.description
            case ast.Constant():
                # Evaluate types expressed as strings
                compiled = compile(ast.Expression(parsed), filename="<ast>", mode="eval")
                result = type_name = eval(compiled)
                parsed = ast.parse(result, mode="eval").body
            case _:
                return description, type_name

    # if get_origin(type) == Annotated:
    #     for annotation in get_args(type):
    #         if isinstance(annotation, TypeDescription):
    #             return annotation.description
    #     # Strip away annotations
    #     type = get_args(type)[0]
    # return getattr(type, "__name__", str(type))

def parse_eval_type(typ: Any) -> tuple[str | None, str]:
    """
    Given an evaluated type signature, returns a tuple of (value description, type signature).
    """
    description: str | None = None
    type_name: str | None = None

    if get_origin(typ) == Annotated:
        for annotation in get_args(typ):
            if isinstance(annotation, TypeDescription):
                type_name = annotation.description
            elif isinstance(annotation, Description):
                description = annotation.description

        # Strip away annotations
        typ = get_args(typ)[0]

    # If the type name wasn't explicitly annotated, use type.__name__
    return description, type_name or getattr(typ, "__name__", str(typ))

def parse_type(typ: Any) -> tuple[str | None, str]:
    """
    Parses a type signature and returns a tuple of (value description, type signature).
    This function handles both evaluated and unevaluated types.
    """
    if isinstance(typ, str):
        return parse_uneval_type(typ)
    else:
        return parse_eval_type(typ)

def docstring_from_signature(func: Callable[..., Any]) -> Docstring:
    """
    Simulates a Docstring based on the function's signature only.
    This doesn't use the function's docstring, but rather generates a new one based on the function's parameters and return type.
    """
    doc = Docstring()

    signature = inspect.signature(func)

    for param_name, param in signature.parameters.items():
        # type_name, = extract_typename(param.annotation)
        param_description, type_name = parse_type(param.annotation)
        doc.meta.append(
            DocstringParam(
                arg_name=param_name,
                description=param_description,
                default=None
                if param.default is inspect.Signature.empty
                else str(param.default),
                type_name=type_name,
                is_optional=param.default is not inspect.Signature.empty,
                args=["param", param_name]
            )
        )

    ret_description, ret_type = parse_type(signature.return_annotation) if signature.return_annotation is not inspect.Signature.empty else (None, None)
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

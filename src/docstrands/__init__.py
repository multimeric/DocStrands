from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Literal, ParamSpec, Protocol, TypeVar, Any, Generic, Self
from docstring_parser import parse, DocstringStyle as StyleEnum, Docstring, compose
from copy import copy

AnyFunc = Callable[..., Any]
T = TypeVar("T", bound=AnyFunc)

P = ParamSpec("P")
Q = ParamSpec("Q")

R = TypeVar("R")
S = TypeVar("S")

DocstringStyle = Literal[
    "rest",
    "google",
    "numpydoc",
    "epydoc",
    "auto",
]
"Redefinition of DocstringStyle as a Literal"
STYLE_MAP: dict[DocstringStyle, StyleEnum] = {
    "rest": StyleEnum.REST,
    "google": StyleEnum.GOOGLE,
    "numpydoc": StyleEnum.NUMPYDOC,
    "epydoc": StyleEnum.EPYDOC,
    "auto": StyleEnum.AUTO,
}

@dataclass
class ParsedFunc(Generic[P, R]):
    """
    Wraps a function with its parsed docstring.
    """
    func: AnyFunc
    docstring: Docstring

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    @property
    def __doc__(self) -> str | None:
        if self.docstring.style is None:
            return self.func.__doc__
        else:
            return compose(self.docstring, self.docstring.style)

    def copy_params(self, *params: str) -> Callable[[ParsedFunc[Q, S]], ParsedFunc[Q, S]]:
        """
        Copies parameter documentation from this function to the decorated function.

        Params:
            params: The names of the parameters to copy.
        """
        def decorator(other: ParsedFunc[Q, S]) -> ParsedFunc[Q, S]:
            new_docstring = copy(other.docstring)
            for param in self.docstring.params:
                if param.arg_name in params:
                    new_docstring.meta.append(param)
            return ParsedFunc(
                other.func,
                new_docstring,
            )
        return decorator


def docstring(style: DocstringStyle) -> Callable[[Callable[P, R]], ParsedFunc[P, R]]:
    def decorator(func: Callable[P, R]) -> ParsedFunc[P, R]:
        # func.__parsed_docstring__ = parse(func.__doc__ or "", style)
        return ParsedFunc(func, parse(func.__doc__ or "", STYLE_MAP[style]))
    return decorator

def copy_params(source: AnyFunc, params: list[str], style: DocstringStyle) -> Callable[[T], T]:
    parsed_source = parse(source.__doc__ or "", style)
    def decorator(func: T) -> T:
        parsed = parse(func.__doc__ or "", style)
        parsed.params.append
        return func
    return decorator

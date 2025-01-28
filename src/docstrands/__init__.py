from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Literal, ParamSpec, Protocol, TypeVar, Any, Generic, Self
from docstring_parser import parse, DocstringStyle as StyleEnum, Docstring, compose, DocstringReturns, RenderingStyle
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

    def __post_init__(self) -> None:
        # These need to be true for Griffe to parse the docstring correctly
        self.docstring.blank_after_long_description = True
        self.docstring.blank_after_short_description = True

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    @property
    def __doc__(self) -> str | None:
        if self.docstring.style is None:
            return self.func.__doc__
        else:
            return compose(self.docstring, self.docstring.style, rendering_style=RenderingStyle.CLEAN)

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

    def copy_returns(self) -> Callable[[ParsedFunc[Q, S]], ParsedFunc[Q, S]]:
        """
        Copies the return documentation from this function to the decorated function.
        """
        def decorator(other: ParsedFunc[Q, S]) -> ParsedFunc[Q, S]:
            new_docstring = copy(other.docstring)
            if self.docstring.returns is None:
                raise ValueError("No return documentation to copy.")
            # Remove any existing return documentation
            new_docstring.meta = list(filter(lambda x: not isinstance(x, DocstringReturns), new_docstring.meta))
            # Add the new return documentation
            new_docstring.meta.append(self.docstring.returns)
            return ParsedFunc(
                other.func,
                new_docstring,
            )
        return decorator

    def copy_synopsis(self) -> Callable[[ParsedFunc[Q, S]], ParsedFunc[Q, S]]:
        """
        Copies the synopsis (first line) from this function to the decorated function.
        """
        def decorator(other: ParsedFunc[Q, S]) -> ParsedFunc[Q, S]:
            new_docstring = copy(other.docstring)
            if self.docstring.short_description is None:
                raise ValueError("No synopsis to copy.")
            new_docstring.short_description = self.docstring.short_description
            return ParsedFunc(
                other.func,
                new_docstring,
            )
        return decorator

    def copy_description(self) -> Callable[[ParsedFunc[Q, S]], ParsedFunc[Q, S]]:
        """
        Copies the description (everything after the synopsis that isn't in a dedicated block) from this function to the decorated function.
        """
        def decorator(other: ParsedFunc[Q, S]) -> ParsedFunc[Q, S]:
            new_docstring = copy(other.docstring)
            if self.docstring.long_description is None:
                raise ValueError("No description to copy.")
            new_docstring.long_description = self.docstring.long_description
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


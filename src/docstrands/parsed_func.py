from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Callable, Literal, Any, Generic, TypeVar
from typing_extensions import ParamSpec
from docstring_parser import (
    parse,
    DocstringStyle as StyleEnum,
    Docstring,
    compose,
    DocstringReturns,
    RenderingStyle,
)
from docstrands.parser_utils import delete_param
from copy import copy
from docstrands.signature import docstring_from_signature
from docstrands.merge import merge_docstrings


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
    Contains a function and its parsed docstring, allowing the docstring to be manipulated.

    In general `ParsedFunc` impersonates the original function, so it can be used in most places where the original function would be used.
    A `ParsedFunc` should only ever be created by the `docstring` decorator.
    """

    func: AnyFunc
    "The original function."
    docstring: Docstring
    "The parsed docstring."

    @classmethod
    def parse(
        cls, func: Callable[P, R], style: DocstringStyle = "auto"
    ) -> ParsedFunc[P, R]:
        _style = STYLE_MAP[style]
        return cls(func=func, docstring=parse(func.__doc__ or "", style=_style))

    def __repr__(self) -> str:
        # This shows up in the help, where we want it to impersonate the original function
        return repr(self.func)

    def __str__(self) -> str:
        # This shows up in the help, where we want it to impersonate the original function
        return str(self.func)

    def __post_init__(self) -> None:
        # These need to be true for Griffe to parse the docstring correctly
        # self.docstring.blank_after_long_description = True
        self.docstring.blank_after_short_description = True

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        # Calling this wrapper should behave like the original function
        return self.func(*args, **kwargs)

    @property
    def __doc__(self) -> str | None:
        if self.docstring.style is None:
            return self.func.__doc__
        else:
            return compose(
                self.docstring,
                self.docstring.style,
                rendering_style=RenderingStyle.CLEAN,
            )

    def copy_params(
        self, *params: str
    ) -> Callable[[ParsedFunc[Q, S]], ParsedFunc[Q, S]]:
        """
        Copies parameter documentation from this function to the decorated function.

        Params:
            params: The names of the parameters to copy.
        """

        def decorator(other: ParsedFunc[Q, S]) -> ParsedFunc[Q, S]:
            new_docstring = copy(other.docstring)
            for param in self.docstring.params:
                if param.arg_name in params:
                    # Delete any existing parameter descriptions with this name
                    delete_param(new_docstring, param.arg_name)
                    new_docstring.meta.append(param)
            return replace(other, docstring=new_docstring)

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
            new_docstring.meta = [x for x in new_docstring.meta if not isinstance(x, DocstringReturns)]
            # Add the new return documentation
            new_docstring.meta.append(self.docstring.returns)
            return ParsedFunc(other.func, new_docstring)

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
            return ParsedFunc(other.func, new_docstring)

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
            return ParsedFunc(other.func, new_docstring)

        return decorator

    def apply_annotations(self) -> None:
        pseudo_docstring = docstring_from_signature(self.func)
        self.docstring = merge_docstrings(self.func, pseudo_docstring, self.docstring)


def docstring(
    style: DocstringStyle, use_annotations: bool = True
) -> Callable[[Callable[P, R]], ParsedFunc[P, R]]:
    """
    Parses the docstring of a function so that it can be manipulated.

    Params:
        style: The style of docstring to parse. One of "rest" (aka Sphinx), "google", "numpydoc" or "epydoc".
        use_annotations: Whether to apply annotations from the function signature.

    Returns:
        A decorator. When this is applied to a function this decorator will return a [`ParsedFunc`][docstrands.ParsedFunc] object.
    """

    def decorator(func: Callable[P, R]) -> ParsedFunc[P, R]:
        ret: ParsedFunc[P, R] = ParsedFunc.parse(func, style)
        if use_annotations:
            ret.apply_annotations()
        return ret

    return decorator

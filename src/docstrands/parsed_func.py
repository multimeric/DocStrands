from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated, Callable, Literal, ParamSpec, Protocol, TypeVar, Any, Generic, Self, get_args, get_origin, get_type_hints
from docstring_parser import DocstringParam, parse, DocstringStyle as StyleEnum, Docstring, compose, DocstringReturns, RenderingStyle
from copy import copy
from docstrands.types import AnyFunc, S, R, P, Q

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

    def __repr__(self) -> str:
        return repr(self.func)
    
    def __str__(self) -> str:
        return str(self.func)

    def __post_init__(self) -> None:
        # These need to be true for Griffe to parse the docstring correctly
        # self.docstring.blank_after_long_description = True
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

    def apply_annotations(self) -> None:
        signature = get_type_hints(self.func, include_extras=True)
        ret_type = signature.pop("return", None)
        if ret_type is not None:
            ret_description = extract_description(ret_type)
            if ret_description is not None:
                # Remove any existing return documentation
                self.docstring.meta = list(filter(lambda x: not isinstance(x, DocstringReturns), self.docstring.meta))
                self.docstring.meta.append(DocstringReturns(args=[], description=ret_description, type_name=None, return_name=None, is_generator=False))
        for param_name, param_type in signature.items():
            param_description = extract_description(param_type)
            if param_description is not None:
                # TODO: remove existing param documentation
                # TODO: refactor this parameter manipulation into a helper function
                self.docstring.meta.append(DocstringParam(args=[], type_name=None, arg_name=param_name, description=param_description, is_optional=False, default=None))


@dataclass
class Description:
    description: str

def extract_description(typ: Any) -> str | None:
    if get_origin(typ) is Annotated:
        for annotation in get_args(typ):
            if isinstance(annotation, Description):
                return annotation.description

def docstring(style: DocstringStyle, use_annotations: bool = True) -> Callable[[Callable[P, R]], ParsedFunc[P, R]]:
    def decorator(func: Callable[P, R]) -> ParsedFunc[P, R]:
        ret: ParsedFunc[P, R] = ParsedFunc(func, parse(func.__doc__ or "", STYLE_MAP[style]))
        if use_annotations:
            ret.apply_annotations()
        return ret
    return decorator


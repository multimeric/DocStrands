from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Annotated, Callable, Literal, Any, Generic, TypeVar, get_args, get_origin, get_type_hints
from typing_extensions import ParamSpec
from docstring_parser import DocstringParam, parse, DocstringStyle as StyleEnum, Docstring, compose, DocstringReturns, RenderingStyle
from copy import copy

from docstrands.annotations import Description, TypeDescription

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

def get_param(doc: Docstring, param_name: str) -> DocstringParam | None:
    """
    Returns an existing parameter definition
    """
    for param in doc.params:
        if param_name == param.arg_name:
            return param

def delete_param(doc: Docstring, param_name: str):
    """
    Deletes any parameters with the given name
    """
    doc.meta = [meta for meta in doc.meta if not (isinstance(meta, DocstringParam) and meta.arg_name == param_name)]

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
                    # Delete any existing parameter descriptions with this name
                    delete_param(new_docstring, param.arg_name)
                    new_docstring.meta.append(param)
            return replace(
                other,
                docstring=new_docstring
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
        try:
            signature = get_type_hints(self.func, include_extras=True)
            # TODO: Use self.func.__annotations__ to parse out the type without evaluating it
        except TypeError as e:
            raise TypeError(f"Error when evaluating the type signature for {self.func.__name__}. Consider using a newer Python version") from e
        if (ret_type := signature.pop("return", None)) is not None and (ret_description := extract_description(ret_type)) is not None:
            # Remove any existing return documentation
            self.docstring.meta = list(filter(lambda x: not isinstance(x, DocstringReturns), self.docstring.meta))
            # args=["returns"] seems to be used by all DocstringReturns
            self.docstring.meta.append(DocstringReturns(args=["returns"], description=ret_description, type_name=extract_typename(ret_type), return_name=None, is_generator=False))
        for param_name, param_type in signature.items():
            param_description = extract_description(param_type)
            type_name = extract_typename(param_type)

            # The parameter we are describing via annotations might already exist in the docstring
            if (existing_param := get_param(self.docstring, param_name)) is None:
                # If it doesn't exist, we create a new one
                # args=["param", param_name] seems to the correct args for DocstringParam
                self.docstring.meta.append(DocstringParam(args=["param", param_name], type_name=type_name, arg_name=param_name, description=param_description, is_optional=False, default=None))
            else:
                # Update the type only if we had no existing description for it, 
                # because what we `type_name` is not guaranteed to be informative
                if existing_param.type_name is None:
                    existing_param.type_name = type_name
                # Update the description if we find any Description,
                # this is likely to be more informative
                if param_description is not None:
                    existing_param.description = param_description


def extract_description(typ: Any) -> str | None:
    if get_origin(typ) is Annotated:
        for annotation in get_args(typ):
            if isinstance(annotation, Description):
                return annotation.description

def extract_typename(type: Any) -> str:
    """
    Strips out any annotations, and returns the name of the type as a string
    """
    if get_origin(type) == Annotated:
        for annotation in get_args(type):
            if isinstance(annotation, TypeDescription):
                return annotation.description
        # Strip away annotations
        type = get_args(type)[0]
    return getattr(type, "__name__", str(type))


def docstring(style: DocstringStyle, use_annotations: bool = True) -> Callable[[Callable[P, R]], ParsedFunc[P, R]]:
    """
    Parses the docstring of a function so that it can be manipulated.

    Params:
        style: The style of docstring to parse. One of "rest" (aka Sphinx), "google", "numpydoc" or "epydoc".
        use_annotations: Whether to apply annotations from the function signature.

    Returns:
        A decorator. When this is applied to a function this decorator will return a [`ParsedFunc`][docstrands.ParsedFunc] object.
    """
    def decorator(func: Callable[P, R]) -> ParsedFunc[P, R]:
        ret: ParsedFunc[P, R] = ParsedFunc(func, parse(func.__doc__ or "", STYLE_MAP[style]))
        if use_annotations:
            ret.apply_annotations()
        return ret
    return decorator


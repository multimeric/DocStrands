

from typing import Any, Callable, ParamSpec, TypeVar


AnyFunc = Callable[..., Any]
T = TypeVar("T", bound=AnyFunc)

P = ParamSpec("P")
Q = ParamSpec("Q")

R = TypeVar("R")
S = TypeVar("S")

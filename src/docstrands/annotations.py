from dataclasses import dataclass
# from typing import Callable, get_type_hints

# from docstring_parser import Docstring
# from docstrands.parsed_func import ParsedFunc
# from docstrands.types import AnyFunc, S, R, P, Q


# def update_with_annotations(parsed_func: ParsedFunc[P, R]) -> ParsedFunc[P, R]:
#     """
#     Updates a ParsedFunc, using Description annotations on the function signature.
#     """
#     signature = get_type_hints(parsed_func.func, include_extras=True)

# def use_annotations() -> Callable[[Callable[P, R] | ParsedFunc[P, R]], ParsedFunc[P, R]]:
#     """
#     A decorator that updates a ParsedFunc with Description annotations on the function signature.
#     """
#     def decorator(func: Callable[P, R] | ParsedFunc[P, R]) -> ParsedFunc[P, R]:
#         if not isinstance(func, ParsedFunc):
#             func = ParsedFunc(func, Docstring())
#         return update_with_annotations(func)
#     return decorator
    
import inspect
from typing import Any, Callable, TypeVar
from docstring_parser import Docstring, DocstringParam, DocstringReturns

def merge_strs(left: str | None, right: str | None) -> str | None:
    """
    Chooses the most informative string, prioritising the right if there is a tie
    """
    # Any None or "" loses to any full string
    return sorted([left, right], key=bool, reverse=True)[0]

T = TypeVar("T", DocstringParam, DocstringReturns)

def merge_meta(left: T | None, right: T | None) -> T:
    match (left, right):
        case (None, None):
            raise ValueError("Cannot merge two None DocstringMeta objects")
        case (None, right):
            return right
        case (left, None):
            return left
        case DocstringParam(), DocstringParam():
            return DocstringParam(
                arg_name=left.arg_name,
                description=merge_strs(left.description, right.description),
                default=merge_strs(left.default, right.default),
                is_optional=left.is_optional or right.is_optional,
                args=["param", left.arg_name],
                type_name=merge_strs(left.type_name, right.type_name)
            )
        case DocstringReturns(), DocstringReturns():
            return DocstringReturns(
                description=merge_strs(left.description, right.description),
                args=[],
                type_name=merge_strs(left.type_name, right.type_name),
                is_generator=left.is_generator or right.is_generator
            )
        case (_, _):
            raise ValueError("Cannot merge different types of DocstringMeta objects")


def merge_docstrings(func: Callable[..., Any], left: Docstring, right: Docstring) -> Docstring:
    """
    Merges two docstrings, preferring the right docstring in case of conflicts.
    """
    signature = inspect.signature(func)

    merged = Docstring()
    merged.short_description = merge_strs(left.short_description, right.short_description)
    merged.long_description = merge_strs(left.long_description, right.long_description)
    merged.blank_after_long_description = right.blank_after_long_description
    merged.blank_after_short_description = right.blank_after_short_description
    merged.style = right.style


    # Merge parameters
    for name in signature.parameters.keys():
        left_param = next((p for p in left.params if p.arg_name == name), None)
        right_param = next((p for p in right.params if p.arg_name == name), None)
        merged_param = merge_meta(left_param, right_param)
        merged.meta.append(merged_param)

    # Merge returns
    merged.meta.append(merge_meta(left.returns, right.returns))

    # Other misc metadata
    merged.meta.extend([meta for meta in left.meta + right.meta if not isinstance(meta, (DocstringParam, DocstringReturns))])

    return merged
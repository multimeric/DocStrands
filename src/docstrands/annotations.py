from dataclasses import dataclass


@dataclass
class Description:
    """
    Allows a description to be attached to any type annotation.
    """
    description: str

@dataclass
class TypeDescription:
    """
    Annotation that can be used to customize how a given type annotation is displayed in the help and in generated documentation.
    """
    description: str
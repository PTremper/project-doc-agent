"""
Dummy module for testing AST traversal and docstring insertion.

This file intentionally contains a variety of Python constructs.
"""

import os
import sys
from functools import cache
from typing import Any

CONSTANT = 42


def simple_function(x: int, y: int) -> int:
    return x + y


def documented_function(name: str) -> str:
    """Return a greeting."""
    return f"Hello {name}"


@cache
def decorated_function(value: str) -> str:
    return value.upper()


async def async_function(delay: float) -> None:
    pass


def multiline_signature(
    first: str,
    second: str,
    *,
    flag: bool = False,
) -> dict[str, Any]:
    return {
        "first": first,
        "second": second,
        "flag": flag,
    }


def outer_function(x: int) -> int:
    """
    Existing outer function docstring.
    """

    def inner_function(y: int) -> int:
        return y * 2

    return inner_function(x)


class SimpleClass:
    pass


class DocumentedClass:
    """Already documented."""

    def method_with_docstring(self) -> str:
        """Existing method docstring."""
        return "hello"

    def undocumented_method(self) -> str:
        return "world"


class ComplexClass:
    CLASS_CONSTANT = "test"

    def __init__(
        self,
        value: str,
    ) -> None:
        self.value = value

    @staticmethod
    def static_method(data: str) -> str:
        return data.strip()

    @classmethod
    def from_value(
        cls,
        value: str,
    ) -> "ComplexClass":
        return cls(value)

    async def async_method(self) -> None:
        pass

    def method_with_nested_function(
        self,
        x: int,
    ) -> int:

        # Nested helper function
        def helper(y: int) -> int:
            return y + 1

        return helper(x)

    class NestedClass:
        def nested_method(self) -> None:
            pass


class DeeplyNested:
    class LevelOne:
        class LevelTwo:
            def target(self) -> None:
                pass


EXPECTED_UNDOCUMENTED = {
    "simple_function",
    "documented_function",
    "decorated_function",
    "async_function",
    "multiline_signature",
    "outer_function",
    "inner_function",
    "SimpleClass",
    "DocumentedClass",
    "DocumentedClass.method_with_docstring",
    "DocumentedClass.undocumented_method",
    "ComplexClass",
    "ComplexClass.__init__",
    "ComplexClass.static_method",
    "ComplexClass.from_value",
    "ComplexClass.async_method",
    "ComplexClass.method_with_nested_function",
    "ComplexClass.helper",
    "ComplexClass.NestedClass",
    "ComplexClass.NestedClass.nested_method",
    "DeeplyNested",
    "DeeplyNested.LevelOne",
    "DeeplyNested.LevelOne.LevelTwo",
    "DeeplyNested.LevelOne.LevelTwo.target",
}

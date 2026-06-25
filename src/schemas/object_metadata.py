from dataclasses import dataclass


@dataclass
class ObjectMetadata:
    """Metadata for a class or function."""

    kind: str
    name: str
    ancestors: str
    parent_class: str | None
    module_name: str
    source_code: str
    module_summary: str
    docstring: str | None

    def __str__(self) -> str:
        """Return the string representation for the dataclass."""
        return (
            "Kind:\n"
            f"{self.kind}\n\n"
            "Name:\n"
            f"{self.name}\n\n"
            "Ancestors:\n"
            f"{self.ancestors}\n\n"
            "Parent Class:\n"
            f"{self.parent_class}\n\n"
            "Module Name:\n"
            f"{self.module_name}\n\n"
            "Source Code:\n"
            f"{self.source_code}\n\n"
            "Module Summary:\n"
            f"{self.module_summary}\n\n"
            "Docstring:\n"
            f"{self.docstring}"
        )


if __name__ == "__main__":
    om = ObjectMetadata(
        kind="function",
        name="my_func_1",
        ancestors="GrandGrandParentClass.GrandParentClass.MyClass",
        parent_class="MyClass",
        module_name="test_module.py",
        source_code="def foo():\n   return 1",
        module_summary="",
        docstring=None,
    )
    print(str(om))  # noqa: T201

from dataclasses import dataclass


@dataclass
class ModuleMetadata:
    """Metadata for a module."""

    path: str
    imports: list[str] | None = None
    classes: list[str] | None = None
    functions: list[str] | None = None
    module_docstring: str | None = None

    def __str__(self) -> str:
        """Return the string representation for the dataclass."""
        imports_str = f"- {'\n- '.join(self.imports)}" if self.imports is not None else None
        classes_str = f"{''.join(self.classes)}" if self.classes is not None else None
        functions_str = f"{''.join(self.functions)}" if self.functions is not None else None

        return (
            "Path:\n"
            f"{self.path}\n\n"
            "Imports:\n"
            f"{imports_str}\n\n"
            "Classes:\n"
            f"{classes_str}\n\n"
            "Functions:\n"
            f"{functions_str}\n\n"
            "Module Docstring:\n"
            f"{self.module_docstring or None}"
        )


if __name__ == "__main__":
    mm = ModuleMetadata(
        path="/path/to/module.py",
        imports=["foo", "bar"],
        classes=["Foo", "Bar"],
        functions=["my_func_1", "my_func_2", "my_func_3"],
        module_docstring="""This is a test docstring""",
    )
    print(str(mm))  # noqa: T201

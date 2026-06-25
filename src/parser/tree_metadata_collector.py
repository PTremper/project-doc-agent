from typing import TYPE_CHECKING, cast, override

import libcst as cst

from src.schemas.module_metadata import ModuleMetadata
from src.schemas.object_metadata import ObjectMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from libcst import ImportAlias


class TreeMetadataCollector(cst.CSTVisitor):
    """Class that traverses a module's tree and extracts metadata about classes and functions."""

    def __init__(self) -> None:
        """Initialize the class with empty dicts and lists to collect metadata when traversing."""
        self._class_stack: list[str] = []
        self.objects_metadata: dict[str, ObjectMetadata] = {}
        self.imports: list[str] = []
        self.module_metadata: ModuleMetadata

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        ancestors = ".".join(self._class_stack)
        obj_full_name = ancestors + "." + node.name.value if ancestors else node.name.value

        self.objects_metadata[obj_full_name] = ObjectMetadata(
            kind="class",
            name=node.name.value,
            ancestors=ancestors,
            parent_class=self._class_stack[-1] if self._class_stack else None,
            module_name="",
            source_code="",
            module_summary="",
            docstring=node.get_docstring(),
        )

        self._class_stack.append(node.name.value)

    @override
    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        self._class_stack.pop()

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        ancestors = ".".join(self._class_stack)
        obj_full_name = ancestors + "." + node.name.value if ancestors else node.name.value

        self.objects_metadata[obj_full_name] = ObjectMetadata(
            kind="function",
            name=node.name.value,
            ancestors=ancestors,
            parent_class=self._class_stack[-1] if self._class_stack else None,
            module_name="",
            source_code="",
            module_summary="",
            docstring=node.get_docstring(),
        )

    @override
    def visit_Import(self, node: cst.Import) -> None:
        self.imports.extend(
            [alias.name.value for alias in node.names if isinstance(alias.name.value, str)],
        )

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        node_names = cast("Sequence[ImportAlias]", node.names)
        self.imports.extend(
            [
                f"{alias.name.value} from {node.module.value}"
                for alias in node_names
                if node.module is not None
            ],
        )

    @override
    def leave_Module(self, original_node: cst.Module) -> None:
        """Generate module metadata from object metadata when leaving the module."""
        # top level functions with nested objects
        functions = [
            _traverse_object_metadata(obj, self.objects_metadata)
            for obj in self.objects_metadata.values()
            if obj.kind == "function" and obj.parent_class is None
        ]

        # top level classes with nested objects
        classes = [
            _traverse_object_metadata(obj, self.objects_metadata)
            for obj in self.objects_metadata.values()
            if obj.kind == "class" and obj.parent_class is None
        ]

        # NOTE that nested function structure is NOT mapped here (yet)
        # this would require adding a self._function_stack = [] and
        # implement the same logic as with self._class_stack
        # and then add parent_function to the ObjectMetadata dataclass
        # and check for that field in the _traverse_object_metadata function

        self.module_metadata = ModuleMetadata(
            path="",
            imports=self.imports,
            classes=classes,
            functions=functions,
            module_docstring=original_node.get_docstring(),
        )

    @override
    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        pass


def _traverse_object_metadata(
    obj_meta: ObjectMetadata,
    module_metadata: dict[str, ObjectMetadata],
    indent_level: int = 0,
) -> str:
    """Build a string representation of a given object's nested classes and functions."""
    children = [obj for obj in module_metadata.values() if obj.parent_class is obj_meta.name]
    ancestry_list = "".join(
        [_traverse_object_metadata(child, module_metadata, indent_level + 1) for child in children],
    )
    return f"{'  ' * indent_level}- {obj_meta.kind} {obj_meta.name}\n{ancestry_list}"


if __name__ == "__main__":
    from src.parser.module_reader import read_script_as_text

    original_code = read_script_as_text("./test_module.py")

    tree = cst.parse_module(original_code)

    collector = TreeMetadataCollector()
    tree.visit(collector)

    print(collector.module_metadata)  # noqa: T201 - allow print statement

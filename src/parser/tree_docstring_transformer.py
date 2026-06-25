from typing import overload, override

import libcst as cst


@overload
def set_docstring(
    original_node: cst.FunctionDef,
    updated_node: cst.FunctionDef,
    new_docstring: str,
    *,
    keep_existing: bool = ...,
) -> cst.FunctionDef: ...


@overload
def set_docstring(
    original_node: cst.ClassDef,
    updated_node: cst.ClassDef,
    new_docstring: str,
    *,
    keep_existing: bool = ...,
) -> cst.ClassDef: ...


def set_docstring(
    original_node: cst.FunctionDef | cst.ClassDef,  # noqa: ARG001 - allow unused argument for consistency with override
    updated_node: cst.FunctionDef | cst.ClassDef,
    new_docstring: str,
    *,
    keep_existing: bool = False,
) -> cst.FunctionDef | cst.ClassDef:
    """Set a docstring on a cst.FunctionDef or cst.ClassDef node."""
    body_statements = list(updated_node.body.body)
    if updated_node.get_docstring() is None:
        body_statements.insert(0, _create_docstring_node(new_docstring))
    elif not keep_existing:
        body_statements[0] = _create_docstring_node(new_docstring)
    else:
        return updated_node
    return updated_node.with_changes(
        body=updated_node.body.with_changes(body=body_statements),
    )


def set_module_docstring(
    original_node: cst.Module,  # noqa: ARG001 - allow unused argument for consistency with override
    updated_node: cst.Module,
    new_docstring: str,
    *,
    keep_existing: bool = False,
) -> cst.Module:
    """Set the module docstring.

    Note:
    ----
    This needs to be a separate function from set_docstring since the first element
    in a function/class node is always indented and thus the replacement needs to take place
    one level deeper.
    The module docstring has no indentation.

    """
    body_statements = list(updated_node.body)
    if updated_node.get_docstring() is None:
        body_statements.insert(0, _create_docstring_node(new_docstring))
    elif not keep_existing:
        body_statements[0] = _create_docstring_node(new_docstring)
    else:
        return updated_node
    return updated_node.with_changes(body=body_statements)


def _create_docstring_node(text: str) -> cst.SimpleStatementLine:
    return cst.SimpleStatementLine(body=[cst.Expr(value=cst.SimpleString(f'"""{text}"""'))])


class TreeDocstringTransformer(cst.CSTTransformer):
    """Class that traverses a module's tree and inserts docstrings into classes and functions."""

    def __init__(self, docstrings: dict[str, str], *, keep_existing: bool = False) -> None:
        """Initialize the class with a dict[full name, docstring] of Docstrings."""
        self.keep_existing = keep_existing
        self._class_stack = []
        self.docstrings = docstrings

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._class_stack.append(node.name.value)

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        self._class_stack.pop()
        # ancestors after popping self from the list
        ancestors = ".".join(self._class_stack)
        obj_full_name = (
            ancestors + "." + original_node.name.value if ancestors else original_node.name.value
        )
        new_docstring = self.docstrings[obj_full_name]

        return set_docstring(
            original_node,
            updated_node,
            new_docstring,
            keep_existing=self.keep_existing,
        )

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        pass

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        ancestors = ".".join(self._class_stack)
        obj_full_name = (
            ancestors + "." + original_node.name.value if ancestors else original_node.name.value
        )
        new_docstring = self.docstrings[obj_full_name]

        return set_docstring(
            original_node,
            updated_node,
            new_docstring,
            keep_existing=self.keep_existing,
        )

    @override
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        if (new_docstring := self.docstrings.get("module")) is not None:
            return set_module_docstring(
                original_node,
                updated_node,
                new_docstring,
                keep_existing=self.keep_existing,
            )
        return updated_node

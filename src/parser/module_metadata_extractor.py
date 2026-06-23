import ast
from typing import TYPE_CHECKING, Any

from src.parser.module_reader import read_script_as_text

if TYPE_CHECKING:
    from pathlib import Path


def _get_function_info(node: ast.FunctionDef) -> dict[str, Any]:
    return {
        "name": node.name,
        "docstring": ast.get_docstring(node),
        "signature": ast.unparse(node.args),
    }


def extract_module_metadata(path: str | Path) -> str:

    source = read_script_as_text(path)

    tree = ast.parse(source)

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])

        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)

    functions = []
    classes = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(_get_function_info(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(
                {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [
                        _get_function_info(item)
                        for item in node.body
                        if isinstance(item, ast.FunctionDef)
                    ],
                },
            )

    module_docstring = ast.get_docstring(tree)

    return f"""
    Path:
    {path}

    Imports:
    {imports or None}

    Classes:
    {classes or None}

    Functions:
    {functions or None}

    Module Docstring:
    {module_docstring}

    """

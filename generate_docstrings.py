import argparse
import ast
import difflib
import json
import shutil  # for validating patch files
import subprocess  # for validating patch files
from dataclasses import dataclass
from pathlib import Path
from typing import override

import libcst as cst
import yaml
from tqdm import tqdm

from src.models.registry import discover_clients
from src.parser.module_metadata_extractor import extract_module_metadata
from src.parser.module_reader import read_script_as_text
from src.utils.initialize_llm import initialize_llm

# @dataclass
# class DocstringTarget:
#     kind: str
#     name: str
#     parent_class: str | None
#     module_name: str
#     source_code: str
#     module_summary: str
#     ast_overview: str


# fmt: off
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docmentation for a Python project.")
    parser.add_argument("file_path", type=str,
        help="Path to the Python file to generate docstrings for.")
    parser.add_argument("--keep_existing", action="store_true",
        help="Keep existing docstrings if they already exist in the target files.")
    return parser.parse_args()
# fmt: on


def set_docstring(original_node, updated_node, new_docstring, keep_existing=False):
    body_statements = list(updated_node.body.body)
    if original_node.get_docstring() is None:
        body_statements.insert(0, create_docstring_node(new_docstring))
    elif not keep_existing:
        body_statements[0] = create_docstring_node(new_docstring)
    return updated_node.with_changes(
        body=updated_node.body.with_changes(body=body_statements),
    )


def create_docstring_node(text: str) -> cst.SimpleStatementLine:
    return cst.SimpleStatementLine(body=[cst.Expr(value=cst.SimpleString(f'"""{text}"""'))])


class DocstringVisitor(cst.CSTVisitor):
    """Class that traverses a module's tree and extracts metadata about classes and functions."""

    def __init__(self):
        self.class_stack = []
        self.module_metadata = {}

    @override
    def visit_ClassDef(self, node):
        ancestors = ".".join(self.class_stack) + "." if self.class_stack else ""

        self.module_metadata[ancestors + node.name.value] = {
            "kind": "class",
            "name": node.name.value,
            "parent_class": self.class_stack[-1] if self.class_stack else None,
            "module_name": "",
            "source_code": "",
            "module_summary": "",
            "ast_overview": "",
            "docstring": node.get_docstring(),
        }

        self.class_stack.append(node.name.value)

    @override
    def leave_ClassDef(self, original_node):
        self.class_stack.pop()

    @override
    def visit_FunctionDef(self, node):
        ancestors = ".".join(self.class_stack) + "." if self.class_stack else ""

        self.module_metadata[ancestors + node.name.value] = {
            "kind": "function",
            "name": node.name.value,
            "parent_class": self.class_stack[-1] if self.class_stack else None,
            "module_name": "",
            "source_code": "",
            "module_summary": "",
            "ast_overview": "",
            "docstring": node.get_docstring(),
        }

    @override
    def leave_FunctionDef(self, original_node):
        pass


class DocstringTransformer(cst.CSTTransformer):
    """Class that traverses a module's tree and inserts docstrings into classes and functions."""

    def __init__(self, docstrings: dict, keep_existing=False):
        self.keep_existing = keep_existing
        self.class_stack = []
        self.docstrings = docstrings

    @override
    def visit_ClassDef(self, node):
        self.class_stack.append(node.name.value)

    @override
    def leave_ClassDef(self, original_node, updated_node):
        self.class_stack.pop()
        # ancestors after popping self from the list
        ancestors = ".".join(self.class_stack) + "." if self.class_stack else ""
        new_docstring = self.docstrings[ancestors + original_node.name.value]

        return set_docstring(original_node, updated_node, new_docstring, self.keep_existing)

    @override
    def visit_FunctionDef(self, node):
        pass

    @override
    def leave_FunctionDef(self, original_node, updated_node):
        ancestors = ".".join(self.class_stack) + "." if self.class_stack else ""
        new_docstring = self.docstrings[ancestors + original_node.name.value]
        return set_docstring(original_node, updated_node, new_docstring, self.keep_existing)


def main():
    # three options:
    # - only new docstrings
    # - completely new docstrings
    # (- also rework old ones using them as context)
    # at first, only the first two options

    # populate the registry with available LLM classes
    discover_clients()

    args = _parse_args()
    target_file_path = args.file_path
    keep_existing = args.keep_existing
    # -----------------------------------------------------------------------
    # first pass extract only and write to disk in outputs
    # llm on those
    # second pass transform and write patch file

    # -----------------------------------------------------------------------
    # stage 1: traverse tree and write to disk

    original_module_path = Path(target_file_path).expanduser()
    module_path = Path(original_module_path.stem + "_copy.py").expanduser()
    original_module_path.copy(module_path, preserve_metadata=True)

    original_code = read_script_as_text(module_path)

    tree = cst.parse_module(original_code)

    visitor = DocstringVisitor()
    tree.visit(visitor)

    # print(visitor.metadata)

    # # -----------------------------------------------------------------------
    # # stage 2: llm
    system_prompt_path = Path("system_prompts")
    config = yaml.safe_load(Path("config/config.yaml").read_text())

    llm = initialize_llm(config=config, llm_task="docstring_llm")

    module_metadata = extract_module_metadata(module_path)
    code = read_script_as_text(module_path)

    new_docstrings = {}

    try:
        # module docstring
        system_prompt = (system_prompt_path / "module_docstring.md").read_text()
        context = (
            f"module name: {module_path.stem}\n"
            f"module code: {code}\n"
            f"module structure: {module_metadata}"
        )
        messages = llm.build_prompt(system_prompt=system_prompt, context=context)
        new_docstrings["module"] = llm.generate(messages)

        for obj, meta in tqdm(visitor.module_metadata.items()):
            match meta.get("kind"):
                case "class":
                    system_prompt = (system_prompt_path / "class_docstring.md").read_text()
                case "function":
                    system_prompt = (system_prompt_path / "function_docstring.md").read_text()
                case None:
                    msg = f"Kind not specified for {obj}. Got None."
                    raise ValueError(msg)
                case _:
                    msg = f"Unsupported kind for {obj}: {meta.get('kind')}"
                    raise ValueError(msg)

            # abstract this construction away into a 'build_context' function
            context = (
                f"kind: {meta.get('kind')}\n"
                f"name: {meta.get('name')}\n"
                f"parent_class: {meta.get('parent_class')}\n"
                f"module name: {module_path.stem}\n"
                f"module code: {code}"
                # f"module_summary"
                # f"ast_overview"
                # f"docstring: {meta.get('docstring')}"
            )

            messages = llm.build_prompt(system_prompt=system_prompt, context=context)
            new_docstrings[obj] = llm.generate(messages)

    finally:
        llm.close_client()

    # save docstring dict to file as json
    docstrings_dir = Path("outputs/docstrings")
    docstrings_dir.mkdir(parents=True, exist_ok=True)
    (docstrings_dir / (module_path.stem + ".json")).write_text(json.dumps(new_docstrings))
    # # -----------------------------------------------------------------------
    # stage 3: traverse, apply and write patch file

    # set module docstring
    if (new_module_docstring := new_docstrings.get("module")) is not None:
        body_statements = list(tree.body)
        if tree.get_docstring() is None:
            body_statements.insert(0, create_docstring_node(new_module_docstring))
        elif not keep_existing:
            body_statements[0] = create_docstring_node(new_module_docstring)
        tree = tree.with_changes(body=body_statements)

    transformer = DocstringTransformer(docstrings=new_docstrings, keep_existing=keep_existing)
    transformed_tree = tree.visit(transformer)

    modified_code = transformed_tree.code

    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        modified_code.splitlines(keepends=True),
        fromfile=str(module_path),
        tofile=str(module_path),
    )

    patch_text = "".join(diff)
    patch_path = Path(module_path.stem + ".patch")
    patch_path.write_text(patch_text)


def test_extraction():
    print("Testing class and function detection...")
    from test_module import EXPECTED_UNDOCUMENTED

    module_path = Path("./test_module.py").expanduser()
    code = read_script_as_text(module_path)
    tree = cst.parse_module(code)

    visitor = DocstringVisitor()
    tree.visit(visitor)

    undocumented = set(EXPECTED_UNDOCUMENTED) - visitor.metadata.keys()
    discovered_but_not_present = set(visitor.metadata.keys()) - EXPECTED_UNDOCUMENTED
    assert undocumented == discovered_but_not_present == set()

    if undocumented != discovered_but_not_present:
        print(f"Undocumented functions: {undocumented}\n")
        print(f"Discovered but not present functions: {discovered_but_not_present}\n")
        print(f"Expected: {sorted(EXPECTED_UNDOCUMENTED)}\n")
        print(f"Found: {sorted(visitor.metadata.keys())}")
    else:
        print("All functions and classes found as expected.")


def test_generating_patch():

    KEEP_EXISTING = False

    original_module_path = Path("./test_module.py").expanduser()
    module_path = Path("./test_module_copy.py").expanduser()
    original_module_path.copy(module_path, preserve_metadata=True)

    original_code = read_script_as_text(module_path)

    tree = cst.parse_module(original_code)

    visitor = DocstringVisitor()
    tree.visit(visitor)
    metadata = visitor.module_metadata
    new_docstrings = {key: "dummy docstring" for key in metadata}

    # set module docstring
    new_docstring = """NEW MODULE DOCSTRING"""

    body_statements = list(tree.body)
    if tree.get_docstring() is None:
        body_statements.insert(0, create_docstring_node(new_docstring))
    elif not KEEP_EXISTING:
        body_statements[0] = create_docstring_node(new_docstring)
    tree = tree.with_changes(body=body_statements)

    transformer = DocstringTransformer(docstrings=new_docstrings, keep_existing=False)
    transformed_tree = tree.visit(transformer)

    modified_code = transformed_tree.code

    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        modified_code.splitlines(keepends=True),
        fromfile=str(module_path),
        tofile=str(module_path),
    )

    patch_text = "".join(diff)
    patch_path = Path("./test_module_copy.patch")
    patch_path.write_text(patch_text)

    # test using:
    # patch --dry-run test_module_copy.py < test_module_copy.patch
    # apply with
    # patch test_module_copy.py < test_module_copy.patch


if __name__ == "__main__":
    main()

    # test_extraction()
    # test_generating_patch()

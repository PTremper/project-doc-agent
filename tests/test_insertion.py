import difflib
from pathlib import Path

import libcst as cst

from src.parser.module_reader import read_script_as_text
from src.parser.tree_docstring_transformer import TreeDocstringTransformer
from src.parser.tree_metadata_collector import TreeMetadataCollector


def test_insertion(keep_existing: bool) -> None:
    """Test the docstring injection logic without involving an LLM."""
    test_outputs_dir = Path("./tests/outputs")
    test_outputs_dir.mkdir(exist_ok=True)

    original_module_path = Path("./test_module.py").expanduser()
    module_path = (test_outputs_dir / "test_module_copy.py").expanduser()
    original_module_path.copy(module_path, preserve_metadata=True)

    original_code = read_script_as_text(module_path)

    tree = cst.parse_module(original_code)

    collector = TreeMetadataCollector()
    tree.visit(collector)
    metadata = collector.objects_metadata
    new_docstrings = dict.fromkeys(metadata, "dummy docstring")
    new_docstrings["module"] = "dummy module docstring"

    transformer = TreeDocstringTransformer(docstrings=new_docstrings, keep_existing=keep_existing)
    transformed_tree = tree.visit(transformer)

    modified_code = transformed_tree.code

    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        modified_code.splitlines(keepends=True),
        fromfile=str(module_path),
        tofile=str(module_path),
    )

    patch_text = "".join(diff)
    patch_path = test_outputs_dir / "test_module_copy.patch"
    patch_path.write_text(patch_text)


if __name__ == "__main__":
    keep_existing = False
    test_insertion(keep_existing)

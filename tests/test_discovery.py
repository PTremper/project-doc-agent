from pathlib import Path

import libcst as cst

from src.parser.module_reader import read_script_as_text
from src.parser.tree_metadata_collector import TreeMetadataCollector
from test_module import EXPECTED_UNDOCUMENTED


def test_discovery() -> None:
    """Test traversing the tree and discover functions and classes."""
    print("Testing class and function detection...")

    module_path = Path("./test_module.py").expanduser()
    code = read_script_as_text(module_path)
    tree = cst.parse_module(code)

    collector = TreeMetadataCollector()
    tree.visit(collector)

    undocumented = set(EXPECTED_UNDOCUMENTED) - collector.objects_metadata.keys()
    discovered_but_not_present = set(collector.objects_metadata.keys()) - EXPECTED_UNDOCUMENTED

    assert undocumented == discovered_but_not_present == set()

    if undocumented != discovered_but_not_present:
        print(f"Undocumented functions: {undocumented}\n")
        print(f"Discovered but not present functions: {discovered_but_not_present}\n")
        print(f"Expected: {sorted(EXPECTED_UNDOCUMENTED)}\n")
        print(f"Found: {sorted(collector.objects_metadata.keys())}")
    else:
        print("All functions and classes found as expected.")


if __name__ == "__main__":
    test_discovery()

import argparse
import difflib
import json
from pathlib import Path

import libcst as cst
import yaml
from tqdm import tqdm

from config.logger import logger
from src.models.registry import discover_clients
from src.parser.module_reader import read_script_as_text
from src.parser.tree_docstring_transformer import TreeDocstringTransformer
from src.parser.tree_metadata_collector import TreeMetadataCollector
from src.utils.initialize_llm import initialize_llm


# fmt: off
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docstrings for Python files.")

    parser.add_argument("file_path", type=str,
        help="Path to the Python file to generate docstrings for.")
    parser.add_argument("--keep_existing", action="store_true",
        help="Keep existing docstrings if they already exist in the target files.")

    return parser.parse_args()
# fmt: on


def main():

    # populate the registry with available LLM classes
    discover_clients()

    args = _parse_args()
    target_file_path = args.file_path
    keep_existing = args.keep_existing

    # -----------------------------------------------------------------------
    # stage 1 - CST Analysis: traverse tree and write metadata to disk

    original_module_path = Path(target_file_path).expanduser()
    module_path = Path(original_module_path.stem + "_copy.py").expanduser()
    original_module_path.copy(module_path, preserve_metadata=True)

    original_code = read_script_as_text(module_path)
    tree = cst.parse_module(original_code)
    collector = TreeMetadataCollector()
    tree.visit(collector)

    # -----------------------------------------------------------------------
    # stage 2 - LLM Docstring Generation: generation based on metadata

    system_prompt_path = Path("system_prompts")
    config = yaml.safe_load(Path("config/config.yaml").read_text())

    llm = initialize_llm(config=config, llm_task="docstring_llm")

    module_metadata = str(collector.module_metadata)
    code = read_script_as_text(module_path)

    new_docstrings = {}

    try:
        # module docstring
        system_prompt = (system_prompt_path / "module_docstring.md").read_text()
        context = (
            f"module name:\n{module_path.stem}\n\n"
            f"module code:\n{code}\n\n"
            f"module structure:\n{module_metadata}"
        )
        logger.info("Loading model to write the module, class and function docstrings...")
        # generate llm response
        messages = llm.build_prompt(system_prompt=system_prompt, context=context)
        new_docstrings["module"] = llm.generate(messages)

        # class and function docstrings
        for obj, obj_meta in tqdm(collector.objects_metadata.items()):
            match obj_meta.kind:
                case "class":
                    system_prompt = (system_prompt_path / "class_docstring.md").read_text()
                case "function":
                    system_prompt = (system_prompt_path / "function_docstring.md").read_text()
                case _:
                    msg = f"Unsupported kind for {obj}: {obj_meta.kind}"
                    raise ValueError(msg)

            messages = llm.build_prompt(system_prompt=system_prompt, context=str(obj_meta))
            new_docstrings[obj] = llm.generate(messages)

    finally:
        logger.info("Closing the client...")
        llm.close_client()

    # save docstring dict to file as json
    docstrings_dir = Path("outputs/docstrings")
    docstrings_dir.mkdir(parents=True, exist_ok=True)
    docstrings_file = docstrings_dir / (module_path.stem + ".json")
    docstrings_file.write_text(json.dumps(new_docstrings))
    logger.info(f"Docstrings saved to {docstrings_file}")
    # # -----------------------------------------------------------------------
    # stage 3 - Patch Generation: traverse tree, apply docstrings and write patch file

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
    patch_file = Path(module_path.stem + ".patch")
    patch_file.write_text(patch_text)
    logger.info(f"Docstrings .patch file saved to {patch_file}")

    # test using:
    # patch --dry-run test_module_copy.py < test_module_copy.patch
    # apply with
    # patch test_module_copy.py < test_module_copy.patch


if __name__ == "__main__":
    main()

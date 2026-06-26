import argparse
from pathlib import Path

import libcst as cst
import yaml
from tqdm import tqdm

from config.logger import logger
from src.models.registry import discover_clients
from src.parser.module_reader import read_script_as_text
from src.parser.tree_metadata_collector import TreeMetadataCollector
from src.utils.initialize_llm import initialize_llm


# fmt: off
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive readme for a Python project.",
    )

    parser.add_argument("project_path", type=str,
        help="Path to the project to generate a readme for.")

    return parser.parse_args()
# fmt: on


def main():

    # populate the registry with available LLM classes
    discover_clients()

    args = _parse_args()
    config = yaml.safe_load(Path("config/config.yaml").read_text())

    # define input paths
    project_base_path = Path.expanduser(Path(args.project_path))
    project_folder_name = Path(project_base_path.name)
    system_prompts_path = Path("system_prompts")
    user_prompts_path = Path("user_prompts")

    # define output paths
    readme_dir = "outputs" / project_folder_name / "readme"
    summary_dir = readme_dir / ".summaries"
    summary_dir.mkdir(exist_ok=True, parents=True)

    # identify relevant files
    ignore_folders = config.get("ignore", [])
    module_paths = [
        file
        for file in project_base_path.rglob("*.py")
        if not any(subdir in str(file) for subdir in ignore_folders)
    ]

    # ---------------------------------------------------------------
    # stage 1: write module summaries
    system_prompt = (system_prompts_path / "module_summary.md").read_text()
    llm = initialize_llm(config=config, llm_task="module_summary_llm")

    logger.info("Loading model to write the module summaries...")
    try:
        for module_path in (pbar := tqdm(module_paths)):
            pbar.set_description(f"Processing {module_path.name}")

            original_code = read_script_as_text(module_path)
            tree = cst.parse_module(original_code)
            collector = TreeMetadataCollector()
            tree.visit(collector)

            module_metadata = str(collector.module_metadata)
            code = read_script_as_text(module_path)
            context = f"Module metadata: {module_metadata}\n\nCode:\n\n{code}"

            # generate llm response
            messages = llm.build_prompt(system_prompt=system_prompt, context=context)
            module_summary = llm.generate(messages)

            (summary_dir / (module_path.stem + ".md")).write_text(module_summary)

    finally:
        logger.info("Closing the client...")
        llm.close_client()

    # ---------------------------------------------------------------
    # stage 2: write architecture summary
    all_module_summaries = "\n\nNEXT MODULE SUMMARY:\n\n".join(
        [
            f"# {summary_file.name}\n\n" + summary_file.read_text()
            for summary_file in summary_dir.iterdir()
        ],
    )
    (summary_dir / "all_module_summaries.md").write_text(all_module_summaries)

    system_prompt = (system_prompts_path / "architecture.md").read_text()
    llm = initialize_llm(config=config, llm_task="architecture_summary_llm")

    try:
        logger.info("Loading model to write the architecture summary...")
        # generate llm response
        messages = llm.build_prompt(system_prompt=system_prompt, context=all_module_summaries)
        architecture_summary = llm.generate(messages)

    finally:
        logger.info("Closing the client...")
        llm.close_client()

    # ---------------------------------------------------------------
    # stage 3: write readme
    (summary_dir / "architecture.md").write_text(architecture_summary)

    system_prompt = (system_prompts_path / "module_summary.md").read_text()
    user_prompt = (user_prompts_path / "README_BRIEF.md").read_text()
    full_system_prompt = system_prompt + "\n\n" + user_prompt

    readme_context = (
        f"## Architecture Summary:\n{architecture_summary}\n\n"
        f"## Module Summaries:\n{all_module_summaries}\n\n"
    )

    llm = initialize_llm(config=config, llm_task="readme_llm")

    try:
        logger.info("Loading model to write the readme...")
        # generate llm response
        messages = llm.build_prompt(system_prompt=full_system_prompt, context=readme_context)
        readme = llm.generate(messages)
    finally:
        logger.info("Closing the client...")
        llm.close_client()

    (readme_dir / "README.md").write_text(readme)


if __name__ == "__main__":
    main()

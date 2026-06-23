import argparse
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from tqdm import tqdm

from src.models.registry import discover_clients, get_llm
from src.parser.module_metadata_extractor import extract_module_metadata
from src.parser.module_reader import read_script_as_text

if TYPE_CHECKING:
    from src.models.base import BaseLLM


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docmentation for a Python project.")
    parser.add_argument("project_path", type=str)
    return parser.parse_args()


def _configure_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # logging.FileHandler("app.log"),  # Log to a file
            logging.StreamHandler(),  # Log to the console
        ],
    )
    return logging.getLogger(__name__)


def initialize_llm(config: dict[str, dict[str, str]], llm_task: str) -> BaseLLM:
    """Initialize the LLM for the given task using the given configuration.

    This function wraps checking all the config entries and error handling.
    """
    llm_config = config.get(f"{llm_task}")
    if llm_config is None:
        msg = f"{llm_task} is not configured"
        raise KeyError(msg)
    if (provider := llm_config.get("provider")) is None:
        msg = f"{llm_task}provider is not configured"
        raise KeyError(msg)
    if (model := llm_config.get("model")) is None:
        msg = f"{llm_task} model is not configured"
        raise KeyError(msg)
    if (base_url := llm_config.get("base_url")) is None:
        msg = f"{llm_task} base_url is not configured"
        raise KeyError(msg)
    if (api_key := llm_config.get("api_key")) is None:
        msg = f"{llm_task} api_key is not configured"
        raise KeyError(msg)
    llm_class = get_llm(provider)
    return llm_class(model=model, base_url=base_url, api_key=api_key)


def main():
    logger = _configure_logger()
    parser = _parse_args()
    config = yaml.safe_load(Path("config/config.yaml").read_text())

    ignore_folders = config.get("ignore", [])

    project_base_path = Path.expanduser(Path(parser.project_path))
    project_folder_name = Path(project_base_path.name)
    system_prompt_path = Path("system_prompts")

    # write summaries
    readme_dir = "outputs" / project_folder_name / "readme"
    summary_dir = readme_dir / ".summaries"
    summary_dir.mkdir(exist_ok=True, parents=True)

    module_paths = [
        file
        for file in project_base_path.rglob("*.py")
        if not any(subdir in str(file) for subdir in ignore_folders)
    ]

    # populate the registry with available LLM classes
    discover_clients()

    with (system_prompt_path / "module_summary.md").open("r") as f:
        system_prompt = f.read()

    llm = initialize_llm(config=config, llm_task="module_summary_llm")

    try:
        for module_path in (pbar := tqdm(module_paths)):
            pbar.set_description(f"Processing {module_path.name}")

            module_metadata = extract_module_metadata(module_path)
            code = read_script_as_text(module_path)

            context = f"Module metadata: {module_metadata}\n\nCode:\n\n{code}"

            messages = llm.build_prompt(system_prompt=system_prompt, context=context)
            module_summary = llm.generate(messages)

            filename = module_path.stem + ".md"

            with (summary_dir / filename).open("w") as f:
                f.write(module_summary)
    finally:
        logger.info("Closing the client...")
        llm.close_client()

    # write architecture summary
    all_module_summaries = []
    for summary_file in summary_dir.iterdir():
        with summary_file.open("r") as f:
            all_module_summaries.append(f"# {summary_file.name}\n\n" + f.read())
    all_module_summaries = "\n\nNEXT MODULE SUMMARY:\n\n".join(all_module_summaries)
    with (summary_dir / "all_module_summaries.md").open("w") as f:
        f.write(all_module_summaries)

    with (system_prompt_path / "architecture.md").open("r") as f:
        system_prompt = f.read()

    llm = initialize_llm(config=config, llm_task="architecture_summary_llm")

    try:
        logger.info("Loading model to write the architecture summary...")
        architecture_summary = llm.generate(
            llm.build_prompt(system_prompt=system_prompt, context=all_module_summaries),
        )
    finally:
        logger.info("Closing the client...")
        llm.close_client()
    with (summary_dir / "architecture.md").open("w") as f:
        f.write(architecture_summary)

    # write readme
    audience = "Python developers"
    style = (
        "Professional yet not too laden with technical jargon."
        " The repo should be understandable for everyone who knows some python."
    )
    notes = (
        "The repo name is python-doc-agent. The license is MIT."
        " This repo is intended as a drafting tool and will most likely"
        " not return a 100% accurate readme."
        " The project contains a pyproject.toml and dependencies"
        " are most conveniently installed using uv sync."
    )

    with (system_prompt_path / "module_summary.md").open("r") as f:
        system_prompt = f.read()
        # manual replacements for now. Full jinja templating would be overkill at this stage.
        system_prompt = system_prompt.replace("{{ audience }}", audience)
        system_prompt = system_prompt.replace("{{ style }}", style)
        system_prompt = system_prompt.replace("{{ notes }}", notes)
    readme_context = (
        "## Architecture Summary:\n"
        f"{architecture_summary}\n\n"
        "## Module Summaries:\n"
        f"{all_module_summaries}\n\n"
    )

    llm = initialize_llm(config=config, llm_task="readme_llm")

    try:
        logger.info("Loading model to write the readme...")
        readme = llm.generate(llm.build_prompt(system_prompt=system_prompt, context=readme_context))
    finally:
        logger.info("Closing the client...")
        llm.close_client()
    with (readme_dir / "README.md").open("w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()

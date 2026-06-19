import argparse
import logging
from pathlib import Path

import yaml
from tqdm import tqdm

from llm_clients.lmstudio_client import LMStudioLLM
from system_prompts import (
    architecture_summary_system_prompt,
    module_summary_system_prompt,
    readme_system_prompt,
)


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


def read_project(path: str | Path) -> str:
    return Path(path).read_text()


def main():
    logger = _configure_logger()
    parser = _parse_args()
    config = yaml.safe_load(Path("config.yaml").read_text())

    ignore_folders = config.get("ignore", [])

    project_base_path = Path.expanduser(Path(parser.project_path))
    project_folder_name = Path(project_base_path.name)

    try:
        # write summaries
        system_prompt = module_summary_system_prompt()
        llm = LMStudioLLM(model=config.get("summary_llm", None))

        readme_dir = "outputs" / project_folder_name / "readme"
        summary_dir = readme_dir / ".summaries"
        Path.mkdir(summary_dir, exist_ok=True, parents=True)

        module_paths = [
            file
            for file in project_base_path.rglob("*.py")
            if not any(subdir in str(file) for subdir in ignore_folders)
        ]

        for module_path in (pbar := tqdm(module_paths)):
            pbar.set_description(f"Processing {module_path.name}")

            code = read_project(module_path)

            messages = llm.build_prompt(system_prompt, content=code)
            module_summary = llm.generate(messages)

            filename = module_path.name.replace(".py", ".md")

            with (summary_dir / filename).open("w") as f:
                f.write(module_summary)
    finally:
        logger.info("Closing the client...")
        llm.close_client()

    try:
        # write architecture summary
        system_prompt = architecture_summary_system_prompt()
        llm = LMStudioLLM(model=config.get("architecture_llm", None))

        full_summary = []
        for summary_file in summary_dir.iterdir():
            with summary_file.open("r") as f:
                full_summary.append(f"# {summary_file.name}\n\n" + f.read())

        full_summary = "\n\nNEXT MODULE SUMMARY:\n\n".join(full_summary)

        with (summary_dir / "full_summary.md").open("w") as f:
            f.write(full_summary)

        logger.info("Loading model to write the architecture summary...")
        architecture_summary = llm.generate(llm.build_prompt(system_prompt, content=full_summary))

        with (summary_dir / "architecture.md").open("w") as f:
            f.write(architecture_summary)
    finally:
        logger.info("Closing the client...")
        llm.close_client()

    try:
        # write readme
        audience = "Python developers"
        style = "Professional yet not too laden with technical jargon. The repo should be understandable for everyone who knows some python."
        notes = (
            "The repo name is python-doc-agent. The license is MIT."
            " This repo is intended as a drafting tool and will most likely not return a 100% accurate readme."
            " The project contains a pyproject.toml and dependencies are most conveniently installed using uv sync."
        )
        system_prompt = readme_system_prompt(audience=audience, style=style, notes=notes)
        llm = LMStudioLLM(model=config.get("readme_llm", None))
        logger.info("Loading model to write the readme...")
        readme = llm.generate(llm.build_prompt(system_prompt, content=architecture_summary))

        with (readme_dir / "README.md").open("w") as f:
            f.write(readme)
    finally:
        logger.info("Closing the client...")
        llm.close_client()


if __name__ == "__main__":
    main()

from pathlib import Path


def read_script_as_text(path: str | Path) -> str:
    """Read a script as text for LLM processing."""
    return Path(path).read_text()

def docstring_system_prompt() -> str:
    """Generate a system prompt to instruct a LLM to write module, class and function docstrings."""
    return (
        "You are writing new google-type docstrings for this Python module."
        "Analyze this module and write a google-type docstring for the module,"
        " as well as for each class and function in it."
        "Return markdown, one heading for each docstring."
    )


def module_summary_system_prompt() -> str:
    """Generate a system prompt to instruct a LLM to summarize a projects modules."""
    return (
        "You are documenting a Python codebase."
        "Analyze this module."
        "Return markdown."
        "## Purpose"
        "(one paragraph)"
        "## Public API"
        "(bullets)"
        "## Key Classes"
        "(bullets)"
        "## Key Functions"
        "(bullets)"
        "## Dependencies"
        "(bullets)"
        "## Notes"
        "(any important implementation details)"
        "CODE:"
    )


def architecture_summary_system_prompt() -> str:
    """Generate a system prompt to instruct a LLM to summary projects architecture."""
    return (
        "You are documenting a Python codebase."
        "Describe the architecture of this project."
        "You will be given summaries of its modules."
        "Return markdown."
        "Please explain:"
        "- major components"
        "- data flow"
        "- dependency relationships"
        "- primary use cases"
        "- extension points"
        "MODULE SUMMARIES:"
    )


def metadata_summary_system_prompt() -> str:
    """Generate a system prompt to instruct a LLM to summarize project metadata."""
    return "You are documenting a Python codebase. Summarize this pyproject.toml file. Return markdown."


# examples / tests system prompts


def readme_system_prompt(
    audience: str = "Python developers",
    style: str = "Professional",
    notes: str = "None",
) -> str:
    """Generate a system prompt to instruct a LLM to write a readme."""
    return (
        "Please write a high quality README for a public python github repo.\n"
        "You will be given a project summary to use as basis for the repo."
        "Audience:\n"
        f"{audience}\n"
        "Style:\n"
        f"{style}\n"
        "Additional instructions:\n"
        f"{notes}\n"
        "Include:\n"
        "- Overview\n"
        "- Features\n"
        "- Installation\n"
        "- Quick Start\n"
        "- Architecture\n"
        "- Examples\n"
        "- Development\n"
        "- License\n\n"
        "Do not invent features.\n\n"
        "Here is the architecture summary of the project:\n\n"
    )

# Project Doc Agent

**Project Doc Agent** is an experimental AI-assisted documentation tool for Python projects. It combines static code analysis with configurable LLM pipelines to generate project documentation and suggest high-quality NumPy-style docstrings.

The project is designed around the idea that documenting an entire repository should be a multi-stage process rather than a single prompt. Instead of sending a complete codebase to an LLM, Project Doc Agent incrementally builds an understanding of the project before generating documentation.

> **Project status:** Active prototype. The current implementation produces useful first drafts of README files and docstrings that are intended to be reviewed by a developer before being committed.

---

## Features

### Repository documentation

Generate a draft `README.md` for a Python project using a hierarchical summarization pipeline.

Current pipeline:

1. Analyze every Python module individually.
2. Generate module summaries.
3. Combine module summaries into an architecture summary.
4. Generate a project README from the synthesized architecture.

This approach allows local models with relatively small context windows to reason about larger repositories.

---

### Docstring generation

Generate NumPy-style docstrings for Python source files.

Current capabilities:

* Module docstrings
* Class docstrings
* Function and method docstrings
* Detection of existing docstrings
* Generation of Git-compatible `.patch` files rather than directly modifying source code

The generated patches can be reviewed before being applied, providing a safer workflow than automatic source modification.

---

## Design Goals

The project focuses on three principles:

* **Model agnostic** – configure different LLMs for different stages of the pipeline. 
  * This allows smaller local models to handle code analysis while larger models can be reserved for producing polished user-facing documentation.
  * Models are automatically discovered through a registry-pattern when an adapter class exists that inherits from the BaseLLM class.
* **Configurable** – prompts and pipeline behavior are defined through configuration files.
  * A config yaml file allows specifying the pipeline behavior.
  * Markdown files expose the LLM instructions and allow for easy editing.
* **Safe by default** – generate patches instead of directly rewriting source files.
  * Easy to review
  * Easy to apply using `patch file_name.py < file_name.patch`

---

## Current Architecture

Readme generation workflow:

```text
 Python Repository
        │
        ▼
   CST Analysis
        │
        ▼
 Module Summaries (LLM)
        │
        ▼
Architecture Summary (LLM)
        │
        ▼
 README Generation (LLM)
```

Docstring generation workflow:

```text
  Python Source
        │
        ▼
   CST Analysis
        │
        ▼
Docstring Generation (LLM)
        │
        ▼
  Patch Generation
```

---

## Usage

Generate repository documentation (readme):

```bash
python generate_documentation.py /path/to/project
```

Generate docstrings for a Python file:

```bash
python generate_docstrings.py path/to/module.py
```

The generated output is written as a Git-compatible `.patch` file that can be reviewed before applying.

### Connecting to LLMs
LLMs can easily be added through defining an adapter class which is automatically discovered by the registry. 

First, add a .py file in `src/models/client/`. This file should contain a class:
- with a registry decorator `@register_llm(provider-name)`, imported with `from src.models.registry import register_llm`.
- that is derived from the abstract base class `BaseLLM` imported with `from src.models.base import BaseLLM` in order to expose the required API. 

This will allow the script to automatically detect and use the adapter class. 

Second, edit the `config/config.yaml` file and specify the model and connection details. 

---

## Technologies

* Python
* Local LLM inference (LM Studio)
* Python Concrete Syntax Tree (CST)
* Configurable YAML pipeline
* Prompt templating
* Git patch generation

---

## Roadmap

Planned improvements include:

* Repository-wide docstring generation
* Applying docstrings across entire projects
* Ensure Ruff compliant docstring formatting
* Optional integration of documentation generation and docstring generation into a single pipeline
* Improved repository understanding
* Higher-quality architecture summaries
* Support for additional LLM providers
* More configurable documentation pipelines

---

## Motivation

Large language models are capable of generating high-quality documentation, but repository-scale documentation requires more context than many local models can process in a single prompt.

Project Doc Agent explores a hierarchical approach where information is summarized step-by-step, allowing smaller local models to contribute effectively while keeping the system modular and extensible.

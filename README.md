# Project-Doc-Agent

Generate project documentation from source code using a configurable multi-stage LLM pipeline.

`project-doc-agent` analyzes a Python repository, creates module-level summaries, combines them into an architecture overview, and finally generates a draft `README.md`. The goal is to provide a solid starting point for project documentation while keeping the entire workflow configurable and model-agnostic.

## How It Works

The documentation pipeline consists of three stages:

1. **Module Summarization**

   * Analyze each Python file individually
      * File function and class structure
      * File code content 
   * Generate concise summaries of its purpose and functionality

2. **Architecture Synthesis**

   * Combine module summaries
   * Produce a high-level overview of the project's structure and responsibilities

3. **README Generation**

   * Use the architecture summary as context
   * Generate a draft README describing the project

```text
Python Repository
      │   │
      │   ▼
+ Module Metadata (AST)
      │   │
      ▼   ▼
1. Module Summaries
      │   │
      │   ▼
2. Architecture Summary
      │   │
      │   │
+ User Instructions
  │   │   │
  ▼   ▼   ▼
3. README Draft
```

## Configuration

Pipeline behavior is controlled through a `config.yaml` file.

The LLM for each stage can be configured separately, which allows the usage of local LLMs for code analysis and large cloud LLMs for generating the readme. 

System prompt templates reside in `system_prompts/`.

This allows experimenting with different models and prompts without changing application code.

## Example Usage

```bash
python project_doc_agent.py /path/to/project
```

Generated artifacts are written to the configured output directory and can be reviewed or edited before publication.

## Project Status

`project-doc-agent` is currently an early prototype. The generated documentation is intended to serve as a high-quality draft rather than a fully polished final document. Future improvements will focus on richer repository analysis, better architecture extraction, and higher-quality documentation output. 

### v0.1
Initial functional prototype: pipeline that reads a module, uses LLMs to generate summaries of its files, summarizes them into an architecture summary and drafts a readme. 

### v0.2
- moved llm configuration into config.yaml
- llms now use a registry pattern
  - registered through a decorator
  - automatically discovered in the models/clients/ folder
  - inherit from base class BaseLLM to ensure the necessary class structure

### v0.3
- moved code into src/ folder
- added ast parsing module to feed module metadata to the LLM

### v0.4
- added single file docstring generation using libcst
  - reads a python file, traverses the cst and extracts all functions and classes
  - prompts a LLM to write docstrings for the module, functions and classes
  - traverses the cst a second time and injects the docstrings (without touching the original file)
  - saves the code with docstrings as a .patch file to ensure code cannot be compromised
    - user can inspect the .patch file and
      - check it for errors using `patch --dry-run file_name.py < file_name.patch`
      - and apply it using `patch file_name.py < file_name.patch`
    - At this stage, a copy of the code is created to make development easier and repeatedly test patching

### v0.5
- refactored docstring generation
- introduced dataclasses for module and object metadata
- readme metadata extraction through cst visitor class like in docstring discovery step

- known bug: generate_docstrings for the file tree_docstring_transformer.py throws an obscure error

## Vision

The long-term goal is to create a modular documentation pipeline where different LLMs can be assigned to specialized tasks such as:

* Docstring generation and agentic implementation
* README generation
* API documentation
* ...

This allows smaller local models to handle code analysis while larger models can be reserved for producing polished user-facing documentation.

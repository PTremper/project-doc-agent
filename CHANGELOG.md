# Changelog

## v0.1
Initial functional prototype: pipeline that reads a module, uses LLMs to generate summaries of its files, summarizes them into an architecture summary and drafts a readme. 

## v0.2
- moved llm configuration into config.yaml
- llms now use a registry pattern
  - registered through a decorator
  - automatically discovered in the models/clients/ folder
  - inherit from base class BaseLLM to ensure the necessary class structure

## v0.3
- moved code into src/ folder
- added ast parsing module to feed module metadata to the LLM

## v0.4
- added single file docstring generation using libcst
  - reads a python file, traverses the cst and extracts all functions and classes
  - prompts a LLM to write docstrings for the module, functions and classes
  - traverses the cst a second time and injects the docstrings (without touching the original file)
  - saves the code with docstrings as a .patch file to ensure code cannot be compromised
    - user can inspect the .patch file and
      - check it for errors using `patch --dry-run file_name.py < file_name.patch`
      - and apply it using `patch file_name.py < file_name.patch`
    - At this stage, a copy of the code is created to make development easier and repeatedly test patching

## v0.5
- refactored docstring generation
- introduced dataclasses for module and object metadata
- readme metadata extraction through cst visitor class like in docstring discovery step

- known bug: generate_docstrings for the file tree_docstring_transformer.py throws an obscure error

## v0.6
- updated and reworked README.md
  - moved changelog into a CHANGELOG.md file
- renamed readme generation entry point project_doc_agent.py -> generate_documentation.py

# Project-Doc-Agent

Generate project documentation from source code using a configurable multi-stage LLM pipeline.

`project-doc-agent` analyzes a Python repository, creates module-level summaries, combines them into an architecture overview, and finally generates a draft `README.md`. The goal is to provide a solid starting point for project documentation while keeping the entire workflow configurable and model-agnostic.

## How It Works

The documentation pipeline consists of three stages:

1. **Module Summarization**

   * Analyze each Python file individually
   * Generate concise summaries of its purpose and functionality

2. **Architecture Synthesis**

   * Combine module summaries
   * Produce a high-level overview of the project's structure and responsibilities

3. **README Generation**

   * Use the architecture summary as context
   * Generate a draft README describing the project

```text
Python Repository
      │  
      ▼  
Module Summaries
    │   │
    │   ▼
Architecture Summary
    │   │
    ▼   ▼
README Draft
```

## Configuration

Pipeline behavior is controlled through a `config.yaml` file.

Configuration options include:

* LLM selection per pipeline stage
* Ignored files and directories

System prompt templates resides in `system_prompts.py`.

This allows experimenting with different models and prompts without changing application code.

## Example Usage

```bash
python project_doc_agent.py /path/to/project
```

Generated artifacts are written to the configured output directory and can be reviewed or edited before publication.

## Project Status

### v0.1
`project-doc-agent` is currently an early prototype. The generated documentation is intended to serve as a high-quality draft rather than a fully polished final document. Future improvements will focus on richer repository analysis, better architecture extraction, and higher-quality documentation output. 

### v0.2
- moved llm configuration into config.yaml
- llms now use a registry pattern
  -  registered through a decorator
  - automatically discovered in the models/clients/ folder
  - inherit from base class BaseLLM to ensure the necessary class structure

## Vision

The long-term goal is to create a modular documentation pipeline where different LLMs can be assigned to specialized tasks such as:

* Docstring generation and agentic implementation
* README generation
* API documentation
* ...

This allows smaller local models to handle code analysis while larger models can be reserved for producing polished user-facing documentation.

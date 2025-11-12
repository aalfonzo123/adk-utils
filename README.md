# adk-utils

## Introduction

This is a CLI utility to manage: 
- Reasoning/Agent engine agents. i.e. deploy from source ADK agent to Agent Engine
- Discovery Engine authorizations
- Gemini Enterprise agents
- Vertex AI long running operations

It is mainly a wrapper around REST methods for those functionalities, using these libraries:
- [Requests](https://requests.readthedocs.io/en/latest/) to execute http methods
- [Typer](https://typer.tiangolo.com/), to easily convert Python functions into CLI commands
- [Rich](https://github.com/Textualize/rich), to list items in table format, instead of a raw JSON dump

## How to use

For regular use, execute this "uv tool install":

`uv tool install git+https://github.com/aalfonzo123/adk-utils`

For occasional use, uvx works:

`uvx --from git+https://github.com/aalfonzo123/adk-utils adk-utils`

See also: [uv tools documentation](https://docs.astral.sh/uv/guides/tools/#requesting-different-sources)

## To-dos

- Check [Cyclopts](https://github.com/BrianPugh/cyclopts) as replacement to Typer, to get automatic docstring parsing into parameter help
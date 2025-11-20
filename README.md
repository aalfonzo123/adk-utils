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

# ADK Utils CLI Cheat Sheet

This guide provides a quick reference to the commands available in the ADK Utils CLI. The base command is `python -m adk_utils.main`, which we will refer to as `adk` for brevity.

---

## `agent`

Manage Agents in Google Cloud Discovery Engine.

### `adk agent create-or-update`

Registers or updates an agent.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Agentspace resources.
-   `--gemini-app-id`: (str) The ID of the Gemini app (Discovery Engine engine).
-   `--display-name`: (str) The display name of the agent.
-   `--description`: (str) The description of the agent for the user.
-   `--tool-description`: (str) The description of the agent for the LLM.
-   `--reasoning-engine-id`: (str) The ID of the reasoning engine endpoint.
-   `--reasoning-engine-location`: (str) The Google Cloud location where the ADK deployment resides.
-   `--auth-ids`: (List[str]) A list of authorization resource IDs. Can be specified multiple times.
-   `--icon-uri`: (str, optional) The public URI of the agent's icon.
-   `--existing-agent-id`: (str, optional) The ID of an existing agent to update.

### `adk agent delete`

Deletes an agent.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Agentspace resources.
-   `--gemini-app-id`: (str) The ID of the Gemini app (Discovery Engine engine).
-   `--agent-id`: (str) The ID of the agent to delete.

### `adk agent list`

Lists all agents for a given Gemini App.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Agentspace resources.
-   `--app-id`: (str) The ID of the Gemini app (Discovery Engine engine).

---

## `authorization`

Manage Authorizations for agents.

### `adk authorization list`

Lists all authorizations.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Discovery Engine resources.
-   `--format-raw`: (bool, optional) If True, prints the raw JSON data.

### `adk authorization create`

Creates a new authorization.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Discovery Engine resources.
-   `--auth-id`: (str) The ID for the new authorization.
-   `--client-id`: (str) The OAuth 2.0 client ID.
-   `--client-secret`: (str) The OAuth 2.0 client secret (will be prompted for).
-   `--base-auth-uri`: (str, optional) The base URI for the authorization server.
-   `--token-uri`: (str, optional) The URI for the token server.
-   `--scopes`: (List[str], optional) A list of OAuth 2.0 scopes. Can be specified multiple times.
-   `--format-raw`: (bool, optional) If True, prints the raw JSON data.

### `adk authorization delete`

Deletes an authorization.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Discovery Engine resources.
-   `--auth-id`: (str) The ID of the authorization to delete.

---

## `gemini-app`

Manage Gemini Apps (Discovery Engine Engines).

### `adk gemini-app list`

Lists all Gemini Apps.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the Discovery Engine resources.

---

## `reasoning-engine`

Manage Reasoning Engines in Google Cloud AI Platform.

### `adk reasoning-engine deploy-from-source`

Deploys a reasoning engine from a local source directory.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the reasoning engine.
-   `--source-dir`: (str) The path to the local directory containing the source code.
-   `--name`: (str) The name of the reasoning engine.
-   `--display-name`: (str) The display name of the reasoning engine.
-   `--entrypointModule`: (str, optional) The Python module containing the entrypoint.
-   `--entrypointObject`: (str, optional) The object within the entrypoint module to be invoked.
-   `--requirementsFile`: (str, optional) The name of the requirements file.
-   `--pythonVersion`: (str, optional) The Python version to use.
-   `--process-env-file`: (bool, optional) Excludes the .env file from the tarball and includes its contents in the deployment definition.
-   `--existing-agent-engine-id`: (str, optional) The ID of an existing Agent Engine to redeploy.

### `adk reasoning-engine list`

Lists all reasoning engines.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the AI Platform resources.

### `adk reasoning-engine delete`

Deletes a reasoning engine.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the AI Platform resources.
-   `--agent-engine-id`: (str) The ID of the reasoning engine to delete.
-   `--force`: (bool, optional) If True, forces the deletion.

---

## `ai-lro`

Manage AI Platform Long-Running Operations (LROs).

### `adk ai-lro list`

Lists the most recent LROs.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the AI Platform resources.

### `adk ai-lro follow`

Follows the status of a specific LRO until it completes.

-   `--project-id`: (str) The Google Cloud project ID.
-   `--location`: (str) The Google Cloud location for the AI Platform resources.
-   `--reasoning-engine-id`: (str) The ID of the reasoning engine.
-   `--lro-id`: (str) The ID of the long-running operation to follow.


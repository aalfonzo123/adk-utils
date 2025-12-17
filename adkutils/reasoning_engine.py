from async_typer import AsyncTyper
import os
import json
from .helpers import AiPlatformRequestHelper
from rich.console import Console
from rich.table import Table
from rich import box
from rich import print as rprint
import tarfile
import io
import logging
import base64
from requests.exceptions import HTTPError
from dotenv import dotenv_values
from rich.prompt import Prompt

from . import re_methods

app = AsyncTyper(no_args_is_help=True)


def print_list(data):
    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("R.Engine ID", style="bright_green")
    table.add_column("Display Name")
    table.add_column("Update Time")
    table.add_column("Deployment Info")
    # table.add_column("Class Methods")
    table.add_column("Env vars")

    for item in data.get("reasoningEngines", []):
        name = item["name"].split("/")[-1]
        display_name = item.get("displayName", "N.A")
        updateTime = item.get("updateTime", "N.A")

        spec = item.get("spec", {})
        # class_methods = ", ".join(
        #     [m.get("name", "[no-name]") for m in spec.get("classMethods", [])]
        # )
        sourceCodeSpec = spec.get("sourceCodeSpec", {})
        pythonSpec = sourceCodeSpec.get("pythonSpec", {})
        entrypointModule = pythonSpec.get("entrypointModule")
        entrypointObject = pythonSpec.get("entrypointObject")

        if entrypointModule and entrypointObject:
            deployment_info = f"entrypointModule:{entrypointModule}\nentrypointObject:{entrypointObject}"
        else:
            deployment_info = "?"

        deploymentSpec = spec.get("deploymentSpec", {})
        env = deploymentSpec.get("env", [])
        env_vars = ", ".join([f"{e['name']}: {e['value']}" for e in env])

        table.add_row(name, display_name, updateTime, deployment_info, env_vars)

    console = Console(highlight=False)
    console.print(table)


@app.command()
def list(project_id: str, location: str):
    helper = AiPlatformRequestHelper(project_id, location)
    try:
        data = helper.get("reasoningEngines")
        while True:
            print_list(data)
            if next_page_token := data.get("nextPageToken"):
                show_next = Prompt.ask(
                    "show next page?", choices=["y", "n"], default="n"
                )
                if show_next == "n":
                    break
                data = helper.get("reasoningEngines", {"pageToken": next_page_token})
            else:
                break
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


def exclude_env_filter(tarinfo):
    if tarinfo.name == ".env":
        return None

    return tarinfo


def _create_targz_and_base64encode(source_dir, module_dirname, process_env_file):
    logging.info("Creating in-memory tarfile of source files")
    if process_env_file:
        filter = exclude_env_filter
    else:
        filter = None

    tar_fileobj = io.BytesIO()
    with tarfile.open(fileobj=tar_fileobj, mode="w|gz") as tar:
        tar.add(source_dir, arcname=module_dirname, filter=filter)
    tar_fileobj.seek(0)
    return base64.b64encode(tar_fileobj.read())


@app.command()
def deploy_from_source(
    project_id: str,
    location: str,
    source_dir: str,
    name: str,
    display_name: str,
    entrypoint_module: str = "agent",
    entrypoint_object: str = "app",
    requirementsFile: str = "requirements.txt",
    pythonVersion: str = "3.12",
    process_env_file: bool = True,
    existing_agent_engine_id: str | None = None,
    service_account: str | None = None,
):
    """
    Deploys a reasoning engine from a local source directory.

    Args:
        project_id (str): The Google Cloud project ID.
        location (str): The Google Cloud location for the reasoning engine.
        source_dir (str): The path to the local directory containing the source code.
        name (str): The name of the reasoning engine.
        display_name (str): The display name of the reasoning engine.
        entrypoint_module (str, optional): The Python module containing the entrypoint. Defaults to "agent".
          Note: will internally be converted to "{agent_source_dir}.{entrypoint_module}".
          I.e. "my-interesting-agent.agent"
        entrypoint_object (str, optional): The app object within the entrypoint module to be invoked. Defaults to "app".
        requirementsFile (str, optional): The name of the requirements file. Defaults to "requirements.txt".
          Note: will internally be converted to "{agent_source_dir}/{requirementsFile}".
          Note: Agent Engine is *very* picky with versions,
          and will easily fall into 30m attempts at resolving matching versions
          and fail after that.
          With a proper requiremets.txt, deployment should take only 5 minutes.
          Recommendation: use uv pyproject.toml or a requirements_base.txt file for management,
          and a "uv pip freeze > requirements.txt" to create the file used here
        pythonVersion (str, optional): The Python version to use. Defaults to "3.12".
        process_env_file (bool, optional): Excludes the .env file from the tarball, and includes its contents in the deployment definition. Defaults to True.
        agent_engine_id (str, optional): The ID of an existing Agent Engine to redeploy. If not provided, a new Agent Engine will be created.
    """
    _, module_dirname = os.path.split(os.path.realpath(source_dir))
    payload = {
        "name": name,
        "displayName": display_name,
        "spec": {
            "agentFramework": "google-adk",
            "classMethods": re_methods.AGENT_ENGINE_CLASS_METHODS,
            "deploymentSpec": {},
            "sourceCodeSpec": {
                "inlineSource": {
                    "sourceArchive": _create_targz_and_base64encode(
                        source_dir, module_dirname, process_env_file
                    ).decode("utf-8")
                },
                "pythonSpec": {
                    "version": pythonVersion,
                    "entrypointModule": f"{module_dirname}.{entrypoint_module}",
                    "entrypointObject": entrypoint_object,
                    "requirementsFile": f"{module_dirname}/{requirementsFile}",
                },
            },
        },
    }

    # Note: For reasons unknown, if the .env file is included in the source tarfile,
    # errors are generated for each line, regarding pydantic rules being broken.
    # As a workaround:
    # - The .env file is skipped in the source file
    # - The contents of the .env file are included in the deploymentSpec section of the payload
    if process_env_file:
        spec_env = []
        for k, v in dotenv_values(source_dir + "/.env").items():
            spec_env.append({"name": k, "value": v})

        payload["spec"]["deploymentSpec"]["env"] = spec_env

    if service_account:
        payload["spec"]["serviceAccount"] = service_account

    # Note: there is no updateMask on the patch call. Sadly, optimizations
    # such as updating only env vars do not work. The method fails saying
    # source code is always needed.
    helper = AiPlatformRequestHelper(project_id, location)
    try:
        if existing_agent_engine_id:
            response = helper.patch(
                f"reasoningEngines/{existing_agent_engine_id}", data=payload
            )
        else:
            response = helper.post("reasoningEngines", data=payload)

        name_parts = response["name"].split("/")
        project_number = name_parts[1]
        location = name_parts[3]
        reasoning_engine_id = name_parts[5]
        lro_id = name_parts[7]

        rprint(f"[green]Deployment started[/green]")
        rprint(
            f"To follow status of deployment ai-lro, run [green]adk-utils ai-lro follow {project_number} {location} {reasoning_engine_id} {lro_id}[/green]"
        )
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.command()
def delete(project_id: str, location: str, agent_engine_id: str, force: bool = False):
    helper = AiPlatformRequestHelper(project_id, location)
    try:
        if force:
            params = {"force": "true"}
        else:
            params = None

        response = helper.delete(f"reasoningEngines/{agent_engine_id}", params)
        rprint(f"[green]Agent deleted[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.async_command()
async def remote_prompt(
    project_id: str, location: str, agent_engine_id: str, prompt: str, auth_to_fill: str
):
    """Sends prompt to remote agent engine that was previously deployed.
    This is used as a basic test.
    Fills auth with token created from currently logged in user.
    Note this works even if the auth doesn't even exist yet, it is filled
    in the session as though it does exist.
    Call is made using streaming_agent_run_with_events, so it is basically equivalent
    to the call that Gemini Enterprise does."""
    import vertexai
    import google.auth as auth
    from google.auth.transport import requests as req

    client = vertexai.Client(project=project_id, location=location)

    adk_app = client.agent_engines.get(
        name=f"projects/{project_id}/locations/{location}/reasoningEngines/{agent_engine_id}"
    )

    print(
        f"operation count:{len(adk_app.operation_schemas())}. Note: if 0, deployment was missing classMethods"
    )
    print("-" * 50)
    creds, project_id = auth.default()
    auth_req = req.Request()
    creds.refresh(auth_req)
    access_token = creds.token

    request_json_simple = json.dumps(
        {
            "message": {
                "role": "user",
                "parts": [{"text": prompt}],
            },
            "authorizations": {auth_to_fill: {"accessToken": access_token}},
        }
    )
    async for event in adk_app.streaming_agent_run_with_events(
        request_json=request_json_simple
    ):
        print(json.dumps(event))

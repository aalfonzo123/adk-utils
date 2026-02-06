import json
import time
from cyclopts import App
from rich.live import Live
from rich.table import Table
from .helpers import DiscoveryEngineRequestHelper, paginate
from rich import print as rprint
from requests.exceptions import HTTPError
from pathlib import Path
import yaml
from importlib.resources import files
from .file_utils import resource_write_after_confirm


app = App(
    "data-insights-agent",
    help="commands related to the pre-built data insights agent (not to be confused with agent engine agents)",
)


@app.command
def init():
    """Copies initial config files to the current directory."""
    try:
        ask = True
        for resource in files("adkutils.insights_init_files").iterdir():
            if resource.is_file():
                dest_file = Path(resource.name)

                ask = resource_write_after_confirm(
                    lambda: resource.read_text(),
                    dest_file,
                    ask,
                )
        rprint("[green]Init succeeded[/green]")
    except FileExistsError as e:
        rprint(f"[bright_red]{e}[/bright_red]")


@app.command()
def create_or_update(
    project_id: str,
    location: str,
    gemini_app_id: str,
    display_name: str,
    description: str,
    auth_id: str,
    icon_uri: str | None = None,
    existing_agent_id: str | None = None,
):
    """
    Registers or updates an agent with Agentspace.

    Args:
        project_id (str): The Google Cloud project ID.
        location (str): The Google Cloud location for the Agentspace resources.
        gemini_app_id (str): The ID of the Gemini app (Discovery Engine engine).
        display_name (str): The display name of the agent.
        description (str): The description of the agent for the user.
        tool_description (str): The description of the agent for the LLM.
        reasoning_engine_id (str): The ID of the reasoning engine endpoint.
        reasoning_engine_location (str): The Google Cloud location where the ADK deployment (reasoning engine) resides.
        auth_ids (List[str]): A list of authorization resource IDs.
        icon_uri (str, optional): The public URI of the agent's icon. Defaults to None.
        existing_agent_id (str, optional): The ID of an existing agent to update. If not provided, a new agent will be created.
    """

    try:
        helper = DiscoveryEngineRequestHelper(project_id, location)
        project_num = helper.get_project_number()
        path = Path("insights.yaml")
        if not path.exists():
            raise ValueError("missing insights.yaml file")

        with open(path, "r") as file:
            insights = yaml.safe_load(file)

        payload = {
            "displayName": display_name,
            "description": description,
            "managed_agent_definition": insights,
            "authorizationConfig": {
                "toolAuthorizations": [
                    f"projects/{project_num}/locations/{location}/authorizations/{auth_id}"
                ],
            },
        }
        if icon_uri:
            payload["icon"] = {"uri": icon_uri}

        if existing_agent_id:
            response = helper.patch(
                f"collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents/{existing_agent_id}",
                data=payload,
            )
        else:
            response = helper.post(
                f"collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents",
                data=payload,
            )

        di_agent_id = response["name"].split("/")[-1]
        rprint(
            "[green]Data insights agent registered.\nTo deploy it, use:[/green]\n"
            f"adk-utils data-insights-agent deploy {project_id} {location} {gemini_app_id} {di_agent_id}"
        )
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.command()
def deploy(
    project_id: str,
    location: str,
    gemini_app_id: str,
    di_agent_id: str,
):
    """ """

    try:
        helper = DiscoveryEngineRequestHelper(project_id, location)
        agent_resource_name = f"collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents/{di_agent_id}"
        payload = {
            "name": agent_resource_name,
        }
        response = helper.post(
            f"{agent_resource_name}:deploy",
            data=payload,
        )

        sections = response["name"].split("/")
        project_number = sections[1]
        operation_id = sections[-1]
        rprint(
            "[green]Data insights agent deployment started. To follow status run:[/green]\n"
            f"adk-utils data-insights-agent follow-lro {project_number} {location} {gemini_app_id} {di_agent_id} {operation_id}"
        )
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


def get_list(data):
    print(json.dumps(data))


@app.command()
def list_lro(project_id: str, location: str, format_raw: bool = False):
    helper = DiscoveryEngineRequestHelper(project_id, location)
    paginate(
        lambda params: helper.get("operations", params),
        lambda data: app.console.print(get_list(data)),
        format_raw,
    )


@app.command()
def follow_lro(
    project_id: str,
    location: str,
    gemini_app_id: str,
    di_agent_id: str,
    operation_id: str,
):
    helper = DiscoveryEngineRequestHelper(project_id, location)

    SLEEP = 15
    rprint(f"Updates are made every {SLEEP}s. Times are in UTC.")
    rprint(
        "This will exit when LRO is done. [yellow]To stop following before that, press Ctrl+C[/yellow]"
    )

    lro_data = helper.get(
        f"collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents/{di_agent_id}/operations/{operation_id}"
    )
    print(json.dumps(lro_data))
    # with Live(Table(), auto_refresh=False) as live:
    #     start_time = time.monotonic()
    #     while True:
    #         current_elapsed_seconds = time.monotonic() - start_time
    #         lro_data = helper.get(
    #             f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents/{di_agent_id}/operations/{operation_id}"
    #         )
    #         live.update(get_list({"operations": [lro_data]}), refresh=True)
    #         if lro_data.get("done", False):
    #             break
    #         time.sleep(SLEEP)

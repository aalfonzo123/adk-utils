import typer
from .helpers import DiscoveryEngineRequestHelper, paginate
from rich.console import Console
from rich.table import Table
from rich import box
from rich import print as rprint
from typing_extensions import Annotated
from typing import List, Optional
from requests.exceptions import HTTPError

app = typer.Typer(no_args_is_help=True)


@app.command()
def create_or_update(
    project_id: str,
    location: str,
    gemini_app_id: str,
    display_name: str,
    description: str,
    tool_description: str,
    reasoning_engine_id: str,
    reasoning_engine_location: str,
    auth_ids: Annotated[List[str], typer.Option()] = [],
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

    helper = DiscoveryEngineRequestHelper(project_id, location)
    project_num = helper.get_project_number()
    payload = {
        "displayName": display_name,
        "description": description,
        "adk_agent_definition": {
            "tool_settings": {"tool_description": tool_description},
            "provisioned_reasoning_engine": {
                "reasoning_engine": f"projects/{project_id}/locations/{reasoning_engine_location}/reasoningEngines/{reasoning_engine_id}"
            },
            "authorizations": [
                f"projects/{project_num}/locations/{location}/authorizations/{auth_id}"
                for auth_id in auth_ids
            ],
        },
    }
    if icon_uri:
        payload["icon"] = {"uri": icon_uri}

    try:
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

        rprint(f"[green]Agent registered. Name:{response['name']}[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.command()
def delete(project_id: str, location: str, gemini_app_id: str, agent_id: str):
    helper = DiscoveryEngineRequestHelper(project_id, location)
    try:
        response = helper.delete(
            f"collections/default_collection/engines/{gemini_app_id}/assistants/default_assistant/agents/{agent_id}"
        )
        rprint(f"[green]Agent deleted[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


def print_list(data):
    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("Agent ID", style="bright_green")
    table.add_column("Display Name")
    table.add_column("Reasoning Engine Name")
    table.add_column("Authorizations")
    table.add_column("Update Time")

    for agent in data.get("agents", []):
        name = agent["name"].split("/")[-1]  # Just the agent ID
        display_name = agent.get("displayName", "N.A")
        adk_definition = agent.get("adkAgentDefinition", {})
        update_time = agent.get("updateTime", "N.A")
        provisioned_engine = adk_definition.get("provisionedReasoningEngine", {})
        reasoning_engine_name = provisioned_engine.get("reasoningEngine", "N.A").split(
            "/"
        )[-1]
        authorizations = adk_definition.get("authorizations", [])
        auth_ids = (
            ", ".join([auth.split("/")[-1] for auth in authorizations])
            if authorizations
            else "N.A"
        )

        table.add_row(name, display_name, reasoning_engine_name, auth_ids, update_time)

    console = Console(highlight=False)
    console.print(table)


@app.command()
def list(project_id: str, location: str, app_id: str):
    helper = DiscoveryEngineRequestHelper(project_id, location)
    paginate(
        lambda params: helper.get(
            f"collections/default_collection/engines/{app_id}/assistants/default_assistant/agents",
            params,
        ),
        lambda data: print_list(data),
    )

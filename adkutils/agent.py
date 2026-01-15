from cyclopts import App
from .helpers import DiscoveryEngineRequestHelper, paginate
from rich import print as rprint
from requests.exceptions import HTTPError
from .print_list_helper import (
    col_spec,
    get_table_generic,
    after_last_slash,
    after_last_slash_multi,
)

app = App(
    "agent",
    help="commands related to gemini enterprise agent definitions (not to be confused with agent engine agents)",
)


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
    auth_ids: list[str] = [],
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
        },
        "authorizationConfig": {
            "toolAuthorizations": [
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
        rprint("[green]Agent deleted[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


def print_list(data):
    app.console.print(
        get_table_generic(
            data,
            "agents",
            [
                col_spec("Agent ID", style="bright_green"),
                "Display Name",
                "Reasoning Engine Name",
                "Authorizations",
                "Update Time",
            ],
            [
                ("name", after_last_slash),
                "displayName",
                (
                    "adkAgentDefinition.provisionedReasoningEngine.reasoningEngine",
                    after_last_slash,
                ),
                (
                    "adkAgentDefinition.authorizations",
                    after_last_slash_multi,
                ),
                "updateTime",
            ],
        )
    )


@app.command()
def list(project_id: str, location: str, app_id: str, format_raw: bool = False):
    # TODO: fix ordering
    helper = DiscoveryEngineRequestHelper(project_id, location)
    paginate(
        lambda params: helper.get(
            f"collections/default_collection/engines/{app_id}/assistants/default_assistant/agents",
            params,
        ),
        lambda data: print_list(data),
        format_raw,
    )

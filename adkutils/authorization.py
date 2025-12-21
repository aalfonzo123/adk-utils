import typer
from .helpers import DiscoveryEngineRequestHelper, paginate
from rich.console import Console
from rich.table import Table
from rich import box
from rich import print as rprint
from .rich_utils import rich_format_url
import json
from urllib.parse import urlencode
from typing_extensions import Annotated
from typing import List, Optional
from requests.exceptions import HTTPError

app = typer.Typer(no_args_is_help=True)

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/cloud-platform", "openid"]


def print_list(data, format_raw: bool):
    if format_raw:
        print(json.dumps(data, indent=2))
        return

    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("Auth ID", style="bright_green")
    table.add_column("Client ID", max_width=20, overflow="fold")
    table.add_column("Authorization URI", overflow="fold")

    for auth in data.get("authorizations", []):
        name = auth["name"].split("/")[-1]
        client_id = auth.get("serverSideOauth2", {}).get("clientId", "N.A")
        auth_uri = auth.get("serverSideOauth2", {}).get("authorizationUri", "N.A")
        token_uri = auth.get("serverSideOauth2", {}).get("tokenUri", "N.A")

        table.add_row(name, client_id, rich_format_url(auth_uri))

    console = Console(highlight=False)
    console.print(table)


def generate_auth_uri(client_id: str, scopes: list[str], base_auth_uri: str) -> str:
    """
    Generates the complete authorization URI with the necessary parameters.

    This function constructs the URI based on the example provided in the document,
    which includes static parameters for the OAuth 2.0 flow like response_type,
    access_type, and prompt.

    Args:
        base_auth_uri: The base endpoint for the authorization server,
        client_id: The OAuth 2.0 client identifier issued to the client.
        scopes: A list of strings representing the access scopes required by the application.

    Returns:
        A fully constructed authorization URI string.
    """
    encoded_scopes = " ".join(scopes)

    params = {
        "client_id": client_id,
        "scope": encoded_scopes,
        "include_granted_scopes": "true",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }

    return f"{base_auth_uri}?{urlencode(params)}"


@app.command()
def list(project_id: str, location: str, format_raw: bool = False):
    helper = DiscoveryEngineRequestHelper(project_id, location)
    paginate(
        lambda params: helper.get("authorizations", params),
        lambda data: print_list(data, format_raw),
    )


@app.command()
def create(
    project_id: str,
    location: str,
    auth_id: str,
    client_id: str,
    client_secret: Annotated[
        str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)
    ],
    base_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth",
    token_uri: str = "https://oauth2.googleapis.com/token",
    scopes: Annotated[Optional[List[str]], typer.Option()] = DEFAULT_SCOPES,
    format_raw: bool = False,
):
    helper = DiscoveryEngineRequestHelper(project_id, location)

    auth_uri = generate_auth_uri(
        base_auth_uri=base_auth_uri, client_id=client_id, scopes=scopes
    )

    payload = {
        "name": f"projects/{project_id}/locations/{location}/authorizations/{auth_id}",
        "serverSideOauth2": {
            "clientId": client_id,
            "clientSecret": client_secret,
            "authorizationUri": auth_uri,
            "tokenUri": token_uri,
        },
    }
    try:
        response = helper.post(
            f"authorizations?authorizationId={auth_id}", data=payload
        )
        rprint(f"[green]Authorization created. Name:{response['name']}[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.command()
def delete(project_id: str, location: str, auth_id: str):
    helper = DiscoveryEngineRequestHelper(project_id, location)
    try:
        response = helper.delete(f"authorizations/{auth_id}")
        rprint(f"[green]Authorization deleted[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")

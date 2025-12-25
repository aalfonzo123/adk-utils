from cyclopts import App
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
from .promptpwd import get_password
import os

from urllib.parse import urlparse, parse_qs, urlencode
import requests
from rich.prompt import Prompt

app = App(
    "authorization",
    help="commands related to gemini enterprise authorizations",
)

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
def get_token(
    project_id: str,
    location: str,
    auth_id: str,
    redirect_uri: str = "https://localhost:8080/",
    extra_url_params: dict[str, str] | None = None,
    destination_env_var: str = "GE_AUTH_TOKEN",
):
    """Obtains an OAuth 2.0 token and creates a script to set it as an environment variable.

    This function guides the user through the OAuth 2.0 authorization flow.
    It prints a URL for the user to open in their browser, prompts for the
    redirected URL after authorization, exchanges the authorization code
    for an access token, and then creates a shell script to set the
    access token as an environment variable.

    Args:
        project_id: The Google Cloud project ID.
        location: The location of the authorization resource.
        auth_id: The ID of the authorization resource.
        redirect_uri: The URI to which the OAuth 2.0 provider redirects
            the user after authorization. Defaults to "https://localhost:8080/".
        extra_url_params: An optional dictionary of additional URL parameters
            to include in the authorization URI. I.e. --extra-url-params.lastname smith
        destination_env_var: The name of the environment variable to set
            with the obtained access token. Defaults to "GE_AUTH_TOKEN".
    """
    try:
        rprint(
            "[bright_yellow]WARNINGS:[/bright_yellow]\n"
            "1. This functionality will only work if the redirect_uri is in the list of 'Authorized URIs' in the oauth client config.\n"
            "2. Usually the redirect_uri is localhost, and the redirect will [green]intentionally[/green] fail in the browser. You then copy the resulting url from the browser.\n"
            "3. You will be asked for the oauth client_secret, have it at hand.\n"
        )
        helper = DiscoveryEngineRequestHelper(project_id, location)
        auth = helper.get(f"authorizations/{auth_id}")

        params = {"redirect_uri": redirect_uri} | (extra_url_params or {})
        authorizationUri = (
            auth["serverSideOauth2"]["authorizationUri"] + "&" + urlencode(params)
        )

        print(
            f"Please open the following URL in your browser to authorize the application:\n{authorizationUri}\n"
        )

        # Exchange authorization code for an access token
        parsed_response_url = urlparse(input("\nPaste the full redirected URL here: "))
        if code_values := parse_qs(parsed_response_url.query).get("code"):
            code = code_values[0]
        else:
            raise ValueError("code not found in redirected url")

        client_secret = Prompt.ask(
            "Enter your Google OAuth client secret", password=True
        )
        token_info = requests.post(
            auth["serverSideOauth2"]["tokenUri"],
            data={
                "code": code,
                "client_id": auth["serverSideOauth2"]["clientId"],
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        ).json()

        if "access_token" not in token_info:
            raise ValueError(
                f"access_token not found in response\n{json.dumps(token_info)}"
            )

        script = "set_auth_token_env_var.sh"
        with open(script, "w") as f:
            f.write(f"{destination_env_var}={token_info['access_token']}")
        print(
            f"script written, to activate use:\n"
            f"source ./{script}\n\n"
            "after that, you can use the variable like this:\n"
            f"[your command here] ${destination_env_var}"
        )
    except (HTTPError, ValueError) as e:
        rprint(f"[bright_red]{e}[/bright_red]")


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
    base_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth",
    token_uri: str = "https://oauth2.googleapis.com/token",
    scopes: List[str] = DEFAULT_SCOPES,
):
    client_secret = get_password("client secret")
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
        rprint("[green]Authorization deleted[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")

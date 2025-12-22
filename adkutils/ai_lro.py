from cyclopts import App
from rich.console import Console
from rich.table import Table
from rich import box
from rich.live import Live
from rich import print as rprint
import json
import time

from requests.exceptions import HTTPError
from .helpers import AiPlatformRequestHelper, paginate

app = App(
    "ai-lro",
    help="commands related to ai long running operations",
)


def print_list(data):
    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("LRO IDs", style="bright_green")
    table.add_column("Type")
    table.add_column("Status\nDates")
    table.add_column("Response")

    for item in data.get("operations", []):
        name = "\n".join(item["name"].split("/")[4:])
        metadata = item.get("metadata", {})
        lro_type = (
            metadata.get("@type", "N/A").split(".")[-1].replace("OperationMetadata", "")
        )
        generic_metadata = metadata.get("genericMetadata", {})
        create_time = generic_metadata.get("createTime", "N.A")
        end_time = generic_metadata.get("updateTime", "N.A")
        dates = f"create: {create_time}\nupdate: {end_time}"

        if item.get("done"):
            status = "done"
            error = item.get("error")
            if error:
                status = "[bright_red]error[/bright_red]"
                response = f"code:{error.get('code')}\nmessage:{error.get('message')}"
            item_response = item.get("response")
            if item_response:
                status = "[bright_green]success[/bright_green]"
                response = ""
        else:
            status = "running"
            response = "N/A"

        table.add_row(name, lro_type, status + "\n" + dates, response)

    console = Console(highlight=False)
    console.print(table)


@app.command()
def cancel(project_id: str, location: str, reasoning_engine_id: str, lro_id: str):
    helper = AiPlatformRequestHelper(project_id, location)
    try:
        helper.post(
            f"reasoningEngines/{reasoning_engine_id}/operations/{lro_id}:cancel", None
        )
        rprint("[green]Lro cancelled[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")


@app.command()
def list(project_id: str, location: str):
    helper = AiPlatformRequestHelper(project_id, location)
    paginate(
        lambda params: helper.get("operations", params),
        lambda data: print_list(data),
    )


@app.command()
def follow(project_id: str, location: str, reasoning_engine_id: str, lro_id: str):
    helper = AiPlatformRequestHelper(project_id, location)

    SLEEP = 15
    rprint(f"Updates are made every {SLEEP}s. Times are in UTC.")
    rprint(
        "This will exit when LRO is done. [yellow]To stop following before that, press Ctrl+C[/yellow]"
    )
    with Live(Table(), auto_refresh=False) as live:
        start_time = time.monotonic()
        while True:
            current_elapsed_seconds = time.monotonic() - start_time
            lro_data = helper.get(
                f"reasoningEngines/{reasoning_engine_id}/operations/{lro_id}"
            )
            live.update(print_list({"operations": [lro_data]}), refresh=True)
            if lro_data.get("done", False):
                break
            time.sleep(SLEEP)

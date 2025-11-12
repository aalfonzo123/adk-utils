import typer
from rich.console import Console
from rich.table import Table
from rich import box

from .helpers import DiscoveryEngineRequestHelper

app = typer.Typer(no_args_is_help=True)

def print_list(data):
    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("App ID", style="bright_green")    
    table.add_column("Display Name")
    table.add_column("Data Store IDs")
        
    for item in data.get('engines', []):
        name = item['name'].split('/')[-1]
        display_name = item.get('displayName', 'N.A')
        solution_type = item.get('solutionType', 'N.A')
        data_store_ids = "\n".join([ds.split('/')[-1] for ds in item.get('dataStoreIds', [])]) if item.get('dataStoreIds') else "N.A"

        table.add_row(name,
            display_name,
            data_store_ids)

    console = Console(highlight=False)
    console.print(table)    

@app.command()
def list(project_id: str, location: str):
    helper = DiscoveryEngineRequestHelper(project_id,location)
    print_list(helper.get("collections/default_collection/engines"))
    
    

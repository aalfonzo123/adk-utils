import typer
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
from dotenv import dotenv_values, load_dotenv

app = typer.Typer(no_args_is_help=True)

def print_list(data):
    table = Table(box=box.SQUARE, show_lines=True)
    table.add_column("R.Engine ID", style="bright_green")
    table.add_column("Display Name")
    table.add_column("Update Time")    

    for item in data.get('reasoningEngines', []):
        name = item['name'].split('/')[-1] 
        display_name = item.get('displayName', 'N.A')    
        updateTime = item.get('updateTime', 'N.A')    

        table.add_row(name,
            display_name,
            updateTime)        
    
    console = Console(highlight=False)
    console.print(table)    
    
@app.command()
def list(project_id: str, location: str):
    helper = AiPlatformRequestHelper(project_id,location)
    try:
      print_list(helper.get("reasoningEngines"))
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")     
    

def exclude_env_filter(tarinfo):    
    if tarinfo.name == '.env':
        return None

    return tarinfo

def _create_targz_and_base64encode(source_dir,process_env_file):  
    logging.info("Creating in-memory tarfile of source files")
    if process_env_file:
      filter = exclude_env_filter
    else:
      filter = None

    tar_fileobj = io.BytesIO()
    with tarfile.open(fileobj=tar_fileobj, mode="w|gz") as tar:
        tar.add(source_dir, arcname='', filter=filter)
    tar_fileobj.seek(0)
    return base64.b64encode(tar_fileobj.read())

@app.command()
def deploy_from_source(project_id: str, location: str, source_dir: str, 
                       name: str, display_name: str, 
                       entrypointModule: str = "agent", 
                       entrypointObject: str = "root_agent_adk",
                       requirementsFile: str = "requirements.txt",
                       pythonVersion: str = "3.12",
                       process_env_file: bool = True,
                       existing_agent_engine_id: str = None):
    """
    Deploys a reasoning engine from a local source directory.

    Args:
        project_id (str): The Google Cloud project ID.
        location (str): The Google Cloud location for the reasoning engine.
        source_dir (str): The path to the local directory containing the source code.
        name (str): The name of the reasoning engine.
        display_name (str): The display name of the reasoning engine.
        entrypointModule (str, optional): The Python module containing the entrypoint. Defaults to "agent".
        entrypointObject (str, optional): The object within the entrypoint module to be invoked. Defaults to "root_agent_adk".
        requirementsFile (str, optional): The name of the requirements file. Defaults to "requirements.txt". 
          Note that Agent Engine is *very* picky with versions, 
          and will easily fall into 30m attempts at resolving matching versions
          and fail after that. 
          With a proper requiremets.txt, deployment should take only 5 minutes.
        pythonVersion (str, optional): The Python version to use. Defaults to "3.12".
        process_env_file (bool, optional): Excludes the .env file from the tarball, and includes its contents in the deployment definition. Defaults to True.
        agent_engine_id (str, optional): The ID of an existing Agent Engine to redeploy. If not provided, a new Agent Engine will be created.
    """
  
    payload = {
      "name": name,
      "displayName": display_name,
      "spec": {
        "agentFramework": "google-adk",
        "deploymentSpec": {},
        "sourceCodeSpec": {
          "inlineSource": {
            "sourceArchive": _create_targz_and_base64encode(source_dir, process_env_file).decode('utf-8')
          },
          "pythonSpec": {
            "version": pythonVersion,
            "entrypointModule": entrypointModule,
            "entrypointObject": entrypointObject,
            "requirementsFile": requirementsFile
          }
        }
      }
    }    

    # Note: For reasons unknown, if the .env file is included in the source tarfile,
    # errors are generated for each line, regarding pydantic rules being broken.
    # As a workaround:
    # - The .env file is skipped in the source file
    # - The contents of the .env file are included in the deploymentSpec section of the payload
    if process_env_file:
      spec_env = []
      for k,v in dotenv_values(source_dir + "/.env").items():
        spec_env.append({"name": k, "value": v})
        
      payload["spec"]["deploymentSpec"]["env"] = spec_env  
    
    # Note: there is no updateMask on the patch call. Sadly, optimizations
    # such as updating only env vars do not work. The method fails saying
    # source code is always needed.
    helper = AiPlatformRequestHelper(project_id,location)
    try:
        if existing_agent_engine_id:
            response = helper.patch(f"reasoningEngines/{existing_agent_engine_id}", data=payload)
        else:
            response = helper.post("reasoningEngines", data=payload)
        
        name_parts = response['name'].split('/')
        project_number = name_parts[1]
        location = name_parts[3]
        reasoning_engine_id = name_parts[5]
        lro_id = name_parts[7]

        rprint(f"[green]Deployment started[/green]")         
        rprint(f"To follow status of deployment ai-lro, run [green]python adkc.py ai-lro follow {project_number} {location} {reasoning_engine_id} {lro_id}[/green]")
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")    
    

@app.command()
def delete(project_id: str, location: str, agent_engine_id: str, force: bool = False):
    helper = AiPlatformRequestHelper(project_id,location)
    try:      
        if force:
          params = {"force": "true"}
        else:
          params = None
          
        response = helper.delete(f"reasoningEngines/{agent_engine_id}", params)
        rprint(f"[green]Agent deleted[/green]")         
    except HTTPError as e:
        rprint(f"[bright_red]{e.response.text}[/bright_red]")     

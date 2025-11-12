import typer

from . import agent
from . import authorization
from . import gemini_app
from . import reasoning_engine
from . import ai_lro

app = typer.Typer(no_args_is_help=True)
app.add_typer(agent.app, name="agent")
app.add_typer(authorization.app, name="authorization")
app.add_typer(gemini_app.app, name="gemini-app")
app.add_typer(reasoning_engine.app, name="reasoning-engine")
app.add_typer(ai_lro.app, name="ai-lro")


if __name__ == "__main__":
    app()
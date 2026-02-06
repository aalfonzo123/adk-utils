from cyclopts import App
from . import agent
from . import authorization
from . import gemini_app
from . import reasoning_engine
from . import ai_lro
from . import data_insights_agent

app = App()
app.register_install_completion_command()
app.command(agent.app)
app.command(authorization.app)
app.command(gemini_app.app)
app.command(reasoning_engine.app)
app.command(ai_lro.app)
app.command(data_insights_agent.app)

if __name__ == "__main__":
    app()

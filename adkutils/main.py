from cyclopts import App
from . import agent
from . import authorization
from . import gemini_app
from . import reasoning_engine
from . import ai_lro

app = App()
app.command(agent.app)
app.command(authorization.app)
app.command(gemini_app.app)
app.command(reasoning_engine.app)
app.command(ai_lro.app)


if __name__ == "__main__":
    app()


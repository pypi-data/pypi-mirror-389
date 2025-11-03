import os
import typer
import uvicorn
from agentbeats.backend import app as backend_app
from agentbeats.controller import main as controller_main

typer_app = typer.Typer()


@typer_app.command()
def serve():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(backend_app, host=host, port=port)


typer_app.command("run_ctrl")(controller_main)


if __name__ == "__main__":
    typer_app()

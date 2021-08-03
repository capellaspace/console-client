"""
cccc CapellaConsoleClientCLI
"""

from pathlib import Path
import tempfile
from typing import Union, List

import typer

from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import AuthenticationError


class CLICachePaths:
    ROOT = Path.home() / ".capella-console-client"
    JWT = ROOT / "jwt.cache"

    @classmethod
    def write_jwt(cls, jwt: str):
        cls.JWT.parent.mkdir(exist_ok=True)
        cls.JWT.write_text(jwt)
        typer.echo(f"Cached JWT to {cls.JWT}")

    @classmethod
    def load_jwt(cls) -> str:
        return cls.JWT.read_text()


CLIENT = CapellaConsoleClient(no_auth=True, verbose=True)


def auto_auth_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        return
    try:
        CLIENT._sesh.authenticate(token=CLICachePaths.load_jwt(), no_token_check=False)
    # first time or expired token
    except (FileNotFoundError, AuthenticationError):
        CLIENT._sesh.authenticate()
        jwt = CLIENT._sesh.headers["authorization"]
        CLICachePaths.write_jwt(jwt)


app = typer.Typer(callback=auto_auth_callback)


# @app.command()
# def auth(
#     email: str = None,
#     password: str = None,
#     token: str = None
# ):
#     CLIENT._sesh.authenticate(email, password, token, no_token_check=True)
#     CLICachePaths().write_jwt(jwt=CLIENT._sesh.headers['authorization'])


@app.command()
def search():
    ret = CLIENT.search(limit=1, collections=["capella-open-data"])
    typer.echo(ret)


@app.command()
def download(
    order_id: str = None,
    tasking_request_id: str = None,
    collect_id: str = None,
    local_dir: Path = Path(tempfile.gettempdir()),
    include: List[str] = None,
    exclude: List[str] = None,
    override: bool = False,
    threaded: bool = True,
    show_progress: bool = True,
    separate_dirs: bool = True,
    product_types: List[str] = None,
):
    CLIENT.download_products(**locals())


@app.command()
def info(item: str):
    typer.echo(f"Selling item: {item}")


@app.command()
def task(item: str):
    typer.echo(f"Selling item: {item}")


def main():
    app()


if __name__ == "__main__":
    main()

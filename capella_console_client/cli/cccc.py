"""
cccc => CapellaConsoleClientCLI
"""

from pathlib import Path
import tempfile
from typing import Union, List

import typer
import questionary

from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import AuthenticationError

import capella_console_client.cli.settings
from capella_console_client.cli.cache import CLICachePaths
from capella_console_client.cli.search import prompt_search_filter, show_tabulated


# CLIENT SINGLETON
CLIENT = CapellaConsoleClient(no_auth=True, verbose=True)


def auto_auth_callback(ctx: typer.Context):
    if ctx.invoked_subcommand in ("settings", None):
        return
    try:
        CLIENT._sesh.authenticate(token=CLICachePaths.load_jwt(), no_token_check=False)
    # first time or expired token
    except (FileNotFoundError, AuthenticationError):
        CLIENT._sesh.authenticate()
        jwt = CLIENT._sesh.headers["authorization"]
        CLICachePaths.write_jwt(jwt)


app = typer.Typer(callback=auto_auth_callback)
app.add_typer(capella_console_client.cli.settings.app, name="settings")


# TODO: autocomplete option
@app.command()
def search():
    search_kwargs = prompt_search_filter()
    stac_items = CLIENT.search(**search_kwargs)
    show_tabulated(stac_items)


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


# @app.command()
# def task(item: str):
#     typer.echo(f"Selling item: {item}")


def main():
    app()


if __name__ == "__main__":
    main()

"""
cccc => CapellaConsoleClientCLI
"""

import sys
from pathlib import Path
import tempfile
from typing import Union, List
from uuid import UUID
import json

import typer
import questionary

from capella_console_client.exceptions import AuthenticationError
from capella_console_client.enumerations import ProductType, AssetType

from capella_console_client.cli.client_singleton import CLIENT
import capella_console_client.cli.settings
import capella_console_client.cli.search
import capella_console_client.cli.my_searches
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.sanitize import convert_to_uuid_str


def auto_auth_callback(ctx: typer.Context):
    # TODO: how to do this properly
    RETURN_EARLY_ON = (
        '--help',
    )
    if any(ret in sys.argv for ret in RETURN_EARLY_ON):
        return

    if ctx.invoked_subcommand in ("settings", "my-searches", None):
        return
    try:
        CLIENT._sesh.authenticate(token=CLICache.load_jwt(), no_token_check=False)
    # first time or expired token
    except (FileNotFoundError, AuthenticationError):
        CLIENT._sesh.authenticate()
        jwt = CLIENT._sesh.headers["authorization"]
        CLICache.write_jwt(jwt)


app = typer.Typer(callback=auto_auth_callback)
app.add_typer(capella_console_client.cli.settings.app, name="settings")
app.add_typer(capella_console_client.cli.search.app, name="search")
app.add_typer(capella_console_client.cli.my_searches.app, name="my-searches")


@app.command(help='order and download products')
def download(
    order_id: UUID = None,
    tasking_request_id: UUID = None,
    collect_id: UUID = None,
    local_dir: Path = typer.Option(
        Path(tempfile.gettempdir()),
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
    ),
    include: List[AssetType] = None,
    exclude: List[AssetType] = None,
    override: bool = typer.Option(False, "--override"),
    threaded: bool = typer.Option(True, "--no-threaded"),
    show_progress: bool = typer.Option(False, "--progress"),
    separate_dirs: bool = typer.Option(True, "--separate-dirs"),
    product_types: List[ProductType] = None,
):
    cur_locals = locals()

    # core works with uuid_str hence converting here
    cur_locals = convert_to_uuid_str(
        cur_locals, uuid_arg_names=("order_id", "collect_id", "tasking_request_id")
    )
    paths = CLIENT.download_products(**cur_locals)
    print(124)


def main():
    app()


if __name__ == "__main__":
    main()

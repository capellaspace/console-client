"""
cccc => CapellaConsoleClientCLI
"""

import sys
from pathlib import Path
from typing import Union, List
from uuid import UUID
import json

import typer
import questionary

from capella_console_client.exceptions import AuthenticationError
from capella_console_client.enumerations import ProductType, AssetType

from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.config import CURRENT_SETTINGS
import capella_console_client.cli.settings
import capella_console_client.cli.search
import capella_console_client.cli.user_searches.my_search_results
import capella_console_client.cli.user_searches.my_search_queries
import capella_console_client.cli.orders
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.sanitize import convert_to_uuid_str
from capella_console_client.cli.user_searches.core import _load_and_prompt, SearchEntity
from capella_console_client.cli.visualize import show_tabulated
from capella_console_client.cli.search import _prompt_post_search_actions


def auto_auth_callback(ctx: typer.Context):
    # TODO: how to do this properly
    RETURN_EARLY_ON = ("--help",)
    if any(ret in sys.argv for ret in RETURN_EARLY_ON):
        return

    if ctx.invoked_subcommand in (
        "settings",
        "my-search-results",
        "my-search-queries",
        None,
    ):
        return

    if ctx.invoked_subcommand == sys.argv[-1]:
        return

    try:
        CLIENT._sesh.authenticate(token=CLICache.load_jwt(), no_token_check=False)
    # first time or expired token
    except (FileNotFoundError, AuthenticationError):
        auth_kwargs = {}
        if "console_user" in CURRENT_SETTINGS:
            auth_kwargs["email"] = CURRENT_SETTINGS["console_user"]
            typer.echo(f"authenticating as {auth_kwargs['email']}")
        CLIENT._sesh.authenticate(**auth_kwargs)  # type: ignore
        jwt = CLIENT._sesh.headers["authorization"]
        CLICache.write_jwt(jwt)


app = typer.Typer(callback=auto_auth_callback)
app.add_typer(capella_console_client.cli.settings.app, name="settings")
app.add_typer(capella_console_client.cli.search.app, name="search")
app.add_typer(
    capella_console_client.cli.user_searches.my_search_results.app,
    name="my-search-results",
)
app.add_typer(
    capella_console_client.cli.user_searches.my_search_queries.app,
    name="my-search-queries",
)
app.add_typer(capella_console_client.cli.orders.app, name="orders")


@app.command(help="order and download products")
def download(
    order_id: UUID = typer.Option(
        None, help="order id you wish to download all associated products for"
    ),
    tasking_request_id: UUID = typer.Option(
        None,
        help="tasking request id of the task request you wish to download all associated products for",
    ),
    collect_id: UUID = typer.Option(
        None, help="collect id you wish to download all associated products for"
    ),
    local_dir: Path = typer.Option(
        Path(CURRENT_SETTINGS["out_path"]),
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        help="local directory where assets are saved to",
    ),
    include: List[AssetType] = typer.Option(
        None, help="which assets should be downloaded (whitelist)"
    ),
    exclude: List[AssetType] = typer.Option(
        None, help="which assets should excluded from download (blacklist)"
    ),
    override: bool = typer.Option(False, "--override", help="override existing assets"),
    threaded: bool = typer.Option(
        True, "--no-threaded", help="disable parallel downloads"
    ),
    show_progress: bool = typer.Option(
        False, "--progress", help="show download status progressbar"
    ),
    product_types: List[ProductType] = typer.Option(
        None, help="filter by product type(s)"
    ),
    from_saved: bool = typer.Option(
        False, "--from-saved", help="from previously saved search result"
    ),
):
    cur_locals = locals()

    # core works with uuid_str hence converting here
    cur_locals = convert_to_uuid_str(
        cur_locals, uuid_arg_names=("order_id", "collect_id", "tasking_request_id")
    )

    for field in ("from_saved", "interactive"):
        cur_locals.pop(field, None)

    if from_saved:
        paths = _download_from_search(**cur_locals)
    else:
        one_of_required = ("order_id", "tasking_request_id", "collect_id")
        if not any(cur_locals[cur] for cur in one_of_required):
            typer.secho(
                "please provide one of order_id, tasking_request_id or collect_id",
                bold=True,
            )
            raise typer.Exit(code=1)

        paths = CLIENT.download_products(**cur_locals)

    if questionary.confirm(f"would you like to open {local_dir}").ask():
        typer.launch(str(local_dir), locate=True)


def _download_from_search(**kwargs):
    saved, selection = _load_and_prompt(
        f"Which saved searcj would you like to use?",
        search_entity=SearchEntity.result,
        multiple=False,
    )

    order_id = CLIENT.submit_order(
        stac_ids=saved[selection]["data"], check_active_orders=True
    )
    kwargs.pop("order_id", None)
    paths = CLIENT.download_products(order_id=order_id, **kwargs)


def main():
    app()


if __name__ == "__main__":
    main()

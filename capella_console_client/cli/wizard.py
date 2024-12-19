"""

"""

import sys


import typer

from capella_console_client.exceptions import AuthenticationError
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.config import CURRENT_SETTINGS
import capella_console_client.cli.settings
import capella_console_client.cli.user_searches.my_searches
import capella_console_client.cli.orders
import capella_console_client.cli.checkout
import capella_console_client.cli.workflows
from capella_console_client.cli.cache import CLICache
from capella_console_client.logconf import logger


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

    if "console_api_key" in CURRENT_SETTINGS:
        CLIENT._sesh.authenticate(api_key=CURRENT_SETTINGS["console_api_key"], no_token_check=False)
        return


app = typer.Typer(
    help="Interactive wizard for api.capellaspace.com",
    callback=auto_auth_callback,
)
app.add_typer(capella_console_client.cli.settings.app, name="settings")
app.add_typer(
    capella_console_client.cli.user_searches.my_searches.app,
    name="my-searches",
)
app.add_typer(capella_console_client.cli.orders.app, name="orders")
app.add_typer(capella_console_client.cli.workflows.app, name="workflows")


@app.command()
def configure():
    """
    configure capella-console-wizard
    """
    capella_console_client.cli.settings.configure()


def main():
    app()


if __name__ == "__main__":
    main()

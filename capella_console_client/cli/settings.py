from typing import List

import typer
import questionary
from pathlib import Path

from tabulate import tabulate

from capella_console_client.cli.validate import (
    _must_be_type,
    _validate_dir_exists,
    _validate_email,
    _no_selection_bye,
    _at_least_one_selected,
)
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    CLI_SUPPORTED_RESULT_HEADERS,
    CURRENT_SETTINGS,
)


app = typer.Typer(help="fine tune settings")


def _prompt_search_result_headers() -> List[str]:
    choices = [
        questionary.Choice(cur, checked=cur in CURRENT_SETTINGS["search_headers"])
        for cur in CLI_SUPPORTED_RESULT_HEADERS
    ]

    first_checked = next(c for c in choices if c.checked)

    search_result_fields = questionary.checkbox(
        "Which fields would you like to display in the search results table?",
        choices=choices,
        initial_choice=first_checked,
        validate=_at_least_one_selected,
    ).ask()
    _no_selection_bye(search_result_fields)

    return search_result_fields


@app.command()
def show():
    """
    show current settings
    """
    typer.secho("Current settings:\n", underline=True)
    table_data = list(CURRENT_SETTINGS.items())
    typer.echo(
        tabulate(table_data, tablefmt="fancy_grid", headers=["setting", "value"])
    )


@app.command()
def result_table():
    """
    set fields to be displayed by default in search results table as column headers
    """
    search_result_headers = _prompt_search_result_headers()

    CLICache.write_user_settings("search_headers", search_result_headers)
    typer.echo("updated fields that to will be displayed in search results table")


@app.command()
def limit():
    """
    set default limit to be used in searches
    """
    limit = questionary.text(
        "Specify your default search limit (can be overridden):",
        default=str(CURRENT_SETTINGS["limit"]),
        validate=_must_be_type(int),
    ).ask()

    if int(limit) > 0:
        CLICache.write_user_settings("limit", int(limit))
        typer.echo(f"updated default search limit to {limit}")
    else:
        typer.echo("invalid limit")


@app.command()
def user():
    """
    set default user for authentication with Capella Console
    """
    console_user = questionary.path(
        "user on console.capellaspace.com (user@email.com):",
        default=CURRENT_SETTINGS.get("console_user", ""),
        validate=_validate_email,
    ).ask()

    if console_user:
        CLICache.write_user_settings("console_user", console_user)
        typer.echo("updated default user for authentication with Capella Console")
        CLICache.JWT.unlink(missing_ok=True)


@app.command()
def output():
    """
    set default output location for downloads and .json exports
    """
    out_path = questionary.path(
        "Specify the default location for your downloads and .json exports:",
        default=CURRENT_SETTINGS["out_path"],
        validate=_validate_dir_exists,
    ).ask()

    if out_path:
        CLICache.write_user_settings("out_path", out_path)
        typer.echo("updated default output path for .json exports")

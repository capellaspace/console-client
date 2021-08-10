import typer
import questionary
from pathlib import Path

from capella_console_client.cli.validate import (
    _must_be_type,
    _validate_dir_exists
)
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
)


app = typer.Typer(help='fine tune settings')


@app.command()
def result_fields():
    """
    set fields to be displayed by default in search results table
    """
    choices = [
        questionary.Choice(cur, checked=cur in CURRENT_SETTINGS["search_fields"])
        for cur in CLI_SUPPORTED_SEARCH_FILTERS
    ]

    search_result_fields = questionary.checkbox(
        "Which fields would you like to display in the search results table?",
        choices=choices,
    ).ask()

    if search_result_fields:
        CLICache.write_user_settings("search_fields", search_result_fields)
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

    if limit > 0:
        CLICache.write_user_settings("limit", int(limit))
        typer.echo("updated default search limit")
    else:
        typer.echo("invalid limit")


@app.command()
def output():
    """
    set default output location for .json exports
    """
    out_path = questionary.path(
        "Specify your default search limit (can be overridden):",
        default=CURRENT_SETTINGS["out_path"],
        validate=_validate_dir_exists,
    ).ask()

    if out_path:
        CLICache.write_user_settings("out_path", out_path)
        typer.echo("updated default output path for .json exports")
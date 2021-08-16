from typing import List, Dict, Tuple, Any
import json

import typer
from tabulate import tabulate
import questionary

from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.user_searches.core import no_data_info
from capella_console_client.cli.user_searches.core import (
    rename_search_entity,
    SearchEntity,
    _load_and_prompt,
)

app = typer.Typer(help="manage saved search queries")


@app.command()
def list(
    detailed: bool = typer.Option(
        False, "--detailed", help="Show STAC ids of saved search queries"
    )
):
    """
    list previously saved search queries
    """
    saved_search_queries = CLICache.load_my_search_queries()
    if not saved_search_queries:
        no_data_info(search_entity=SearchEntity.query)

    table_data = [
        (k, json.dumps(v, sort_keys=True, indent=4))
        for k, v in saved_search_queries.items()
    ]

    typer.secho("My search queries\n", bold=True)
    typer.echo(
        tabulate(table_data, tablefmt="fancy_grid", headers=["identifier", "query"])
    )
    return saved_search_queries


@app.command()
def rename():
    """
    rename previously saved search result
    """
    rename_search_entity(search_entity=SearchEntity.query)


@app.command()
def delete():
    """
    delete previously saved search query
    """
    saved_search_queries, selection = _load_and_prompt(
        "Which saved search queries would you like to delete?"
    )

    if not selection:
        return

    for selected in selection:
        del saved_search_queries[selected]

    CLICache.write_my_search_queries(saved_search_queries)
    typer.echo(f"Deleted {len(selection)} search queries")


@app.command()
def prune():
    """
    delete ALL previously saved search queries
    """
    if questionary.confirm(
        "Please confirm you'd like to delete ALL of your saved search queries. This action cannot be undone."
    ).ask():
        try:
            CLICache.MY_SEARCH_QUERIES.unlink()
        except FileNotFoundError:
            pass
        typer.echo(f"Deleted ALL saved search queries")

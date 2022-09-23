import typer
from tabulate import tabulate
import questionary

from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.info import no_data_info
from capella_console_client.cli.user_searches.core import (
    rename_search_entity,
    SearchEntity,
    _load_and_prompt,
)
from capella_console_client.logconf import logger


app = typer.Typer(help="manage saved search results")


@app.command()
def list(detailed: bool = typer.Option(False, "--detailed", help="Show STAC ids of saved search results")):
    """
    list previously saved search results
    """
    saved_search_results = CLICache.load_my_search_results()
    if not saved_search_results:
        no_data_info(search_entity=SearchEntity.result)

    table_data = []
    for k, v in saved_search_results.items():
        stac_ids = v["data"]
        cur = [k, v["created_at"], v["updated_at"], f"{len(stac_ids)} items"]
        if detailed:
            cur.append("\n".join(stac_ids))
        table_data.append(cur)

    headers = ["identifier", "created", "updated", "size", "STAC ids"]
    logger.info(typer.style("My saved search results\n", bold=True))
    typer.secho(tabulate(table_data, tablefmt="fancy_grid", headers=headers))
    return saved_search_results


@app.command()
def rename():
    """
    rename previously saved search result
    """
    rename_search_entity(search_entity=SearchEntity.result)


@app.command()
def delete():
    """
    delete previously saved search result
    """
    saved_search_results, selection = _load_and_prompt(
        "Which saved search result would you like to delete?", SearchEntity.result
    )

    if not selection:
        return

    for selected in selection:
        del saved_search_results[selected]

    CLICache.write_my_search_results(saved_search_results)
    suffix = "s" if len(selection) > 1 else ""
    logger.info(f"Deleted the following search result{suffix}:")
    logger.info("\n".join(selected))


@app.command()
def prune():
    """
    delete ALL previously saved search result
    """
    if questionary.confirm(
        "Please confirm you'd like to delete ALL of your saved search results. This action cannot be undone."
    ).ask():
        try:
            CLICache.MY_SEARCH_RESULTS.unlink()
        except FileNotFoundError:
            pass
        logger.info(f"Deleted ALL saved search results")

from typing import List, Dict, Tuple, Any

import typer
from tabulate import tabulate
import questionary

from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import _no_selection_bye

app = typer.Typer(help="manage saved searches")


def _list_impl():
    my_searches = CLICache.load_my_searches()

    if not my_searches:
        typer.secho("No searches currently saved!\n", bold=True)
        typer.echo(f"Issue")
        typer.secho(f"\tcapella-console-wizard search interactive", bold=True)
        typer.echo("\nin order to save your first search.")
        raise typer.Exit(code=1)
    table_data = [(k, f"{len(v)} items") for k, v in my_searches.items()]

    typer.secho("My searches\n\n", bold=True)
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers=["identifier", ""]))
    return my_searches


@app.command()
def list():
    """
    list previously saved searches
    """
    _list_impl()


def _load_and_prompt(
    question: str, multiple: bool = True
) -> Tuple[Dict[str, Any], List[str]]:
    my_searches = _list_impl()
    typer.echo("\n\n")

    question_cls = questionary.checkbox if multiple else questionary.select
    selection = question_cls(message=question, choices=my_searches).ask()
    _no_selection_bye(selection)
    return (my_searches, selection)


@app.command()
def rename():
    """
    rename previously saved searches
    """
    my_searches, selection = _load_and_prompt(
        "Which saved searches would you like to rename?"
    )

    change_cnt = 0
    for selected in selection:
        new_name = questionary.text(
            message=f"Rename {selected} to:",
            default=selected,
            validate=lambda x: x is not None and len(x) > 0,
        ).ask()

        if new_name != selected:
            val = my_searches[selected]
            my_searches[new_name] = val
            del my_searches[selected]
            change_cnt += 1

    if change_cnt > 0:
        CLICache.write_my_searches(my_searches)
        typer.echo(f"Renamed {change_cnt} searches")


@app.command()
def delete():
    """
    delete previously saved searches
    """
    my_searches, selection = _load_and_prompt(
        "Which saved searches would you like to delete?"
    )

    if not selection:
        return

    for selected in selection:
        del my_searches[selected]

    CLICache.write_my_searches(my_searches)
    typer.echo(f"Deleted {len(selection)} searches")

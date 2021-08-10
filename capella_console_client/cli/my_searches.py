from typing import List, Dict, Tuple, Any

import typer
from tabulate import tabulate
import questionary

from capella_console_client.cli.cache import CLICache

app = typer.Typer(help='manage saved searches')


@app.command()
def list(ctx: typer.Context):
    """
    list previously saved searches
    """
    my_searches = CLICache.load_my_searches()

    if not my_searches:
        typer.echo("No searches currently saved in 'my-searches'")
        typer.echo(f"Issue")
        typer.secho(f"\t{ctx.parent.parent.info_name} search interactive", bold=True)
        typer.echo("\nin order to save your first search.")
        return
    table_data = [(k, f'{len(v)} items') for k,v in my_searches.items()]

    typer.secho("My searches\n\n", bold=True)
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers=["identifier", ""]))


def _load_and_prompt(ctx: typer.Context, question: str) -> Tuple[Dict[str, Any], List[str]]:
    ctx.invoke(list)
    
    my_searches = CLICache.load_my_searches()
    typer.echo('\n\n')
    selection = questionary.checkbox(
        message=question,
        choices=my_searches
    ).ask()

    return (my_searches, selection)

@app.command()
def rename(ctx: typer.Context):
    """
    rename previously saved searches
    """
    my_searches, selection = _load_and_prompt(ctx, "Which ones would you like to rename?")

    change_cnt = 0
    for selected in selection:
        new_name = questionary.text(
            message=f"Rename {selected} to:",
            default=selected,
            validate=lambda x: x is not None and len(x) > 0
        ).ask()

        if new_name != selected:
            val = my_searches[selected]
            my_searches[new_name] = val
            del my_searches[selected]
            change_cnt += 1

    if change_cnt > 0:
        CLICache.write_my_searches(my_searches)
        typer.echo(f'Renamed {change_cnt} searches')


@app.command()
def delete(ctx: typer.Context):
    """
    delete previously saved searches
    """
    my_searches, selection = _load_and_prompt(ctx, "Which ones would you like to delete?")

    if not selection:
        return

    for selected in selection:
        del my_searches[selected]
    
    CLICache.write_my_searches(my_searches)
    typer.echo(f'Deleted {len(selection)} searches')
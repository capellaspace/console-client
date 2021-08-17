import typer


def no_data_info(search_entity):
    typer.secho(f"No search {search_entity.name} currently saved!\n", bold=True)
    typer.echo(f"Issue")
    typer.secho(f"\tcapella-console-wizard search interactive", bold=True)
    typer.echo(f"\nin order to search and save your first search {search_entity.name}.")
    raise typer.Exit(code=1)


def download_hint(order_id: str):
    typer.echo(f"Issue")
    typer.secho(f"\tcapella-console-wizard download --order-id {order_id}", bold=True)
    typer.echo("\nin order to download all products of the order.")


def my_search_entity_info(identifier: str):
    txt = f"""Added '{identifier}' to my-search-results and my-search-queries"
Issue

\tcapella-console-wizard my-search-results list

    or

\tcapella-console-wizard my-search-queries list

in order to list your saved search results or queries.
"""
    typer.echo(txt)

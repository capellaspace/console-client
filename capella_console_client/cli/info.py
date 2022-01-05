import typer


def no_data_info(search_entity):
    typer.secho(f"No search {search_entity.name} currently saved!\n", bold=True)
    typer.echo(f"Issue")
    typer.secho(f"\tcapella-console-wizard workflows search", bold=True)
    typer.echo(f"\nin order to search and save your first search {search_entity.name}.")
    raise typer.Exit(code=1)


def download_hint(order_id: str):
    typer.echo(f"Issue")
    typer.secho("\tcapella-console-wizard checkout", bold=True)
    typer.echo(
        f"\n select order 'select existing order' and provide order id {order_id} in order to download all products of the order."
    )


def my_search_entity_info(identifier: str):
    txt = f"""Added '{identifier}' to my-search-results and my-search-queries"
Issue

\tcapella-console-wizard my-search-results list

    or

\tcapella-console-wizard my-search-queries list

in order to list your saved search results or queries.
"""
    typer.echo(txt)

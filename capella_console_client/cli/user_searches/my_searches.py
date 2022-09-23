import typer

import capella_console_client.cli.user_searches.my_search_queries
import capella_console_client.cli.user_searches.my_search_results

app = typer.Typer(help="manage my-searches (queries and results)")
app.add_typer(capella_console_client.cli.user_searches.my_search_queries.app, name="queries")
app.add_typer(capella_console_client.cli.user_searches.my_search_results.app, name="results")

import typer

from capella_console_client.cli.search import interactive_search, from_saved
from capella_console_client.cli.checkout import interactive_search_order_and_download

app = typer.Typer(help="interactive workflows")


@app.command(help="interactively search through the archive")
def search():
    interactive_search()


@app.command(help="re-search a previously saved query")
def search_from_saved():
    from_saved()


@app.command(help="interactively search, order and download workflow")
def checkout():
    interactive_search_order_and_download()

from typing import List, Dict, Any
from collections import defaultdict

import typer
from tabulate import tabulate

from capella_console_client.config import (
    STAC_PREFIXED_BY_QUERY_FIELDS,
)

from capella_console_client.cli.config import (
    CURRENT_SETTINGS,
)


def show_tabulated(stac_items: List[Dict[str, Any]], search_headers: List[str] = None):
    if not search_headers:
        search_headers = CURRENT_SETTINGS["search_headers"]

    table_data = defaultdict(list)

    # force id left if specified
    if "id" in search_headers:
        del search_headers[search_headers.index("id")]
        search_headers.insert(0, "id")

    for field in search_headers:
        for it in stac_items:
            if field in STAC_PREFIXED_BY_QUERY_FIELDS:
                value = it["properties"].get(STAC_PREFIXED_BY_QUERY_FIELDS[field])
            else:
                value = it.get(field, "n/a")

            if value is not None:
                table_data[field].append(value)

    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers="keys"))
    typer.echo("\n")

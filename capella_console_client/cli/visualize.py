from typing import List, Dict, Any, Optional
from collections import defaultdict

import typer
from tabulate import tabulate

from capella_console_client.config import (
    STAC_PREFIXED_BY_QUERY_FIELDS,
)
from capella_console_client.search import SearchResult

from capella_console_client.cli.config import (
    CURRENT_SETTINGS,
)


def show_tabulated(
    stac_items: SearchResult,
    search_headers: Optional[List[str]] = None,
    show_row_number: bool = False,
):
    if not search_headers:
        search_headers = CURRENT_SETTINGS["search_headers"]  # type: ignore

    table_data = defaultdict(list)

    assert search_headers is not None
    # force id left if specified
    if "id" in search_headers:
        del search_headers[search_headers.index("id")]
        search_headers.insert(0, "id")

    if show_row_number:
        table_data["#"] = list(range(1, len(stac_items) + 1))

    for field in search_headers:
        for it in stac_items:
            if field in STAC_PREFIXED_BY_QUERY_FIELDS:
                value = it["properties"].get(STAC_PREFIXED_BY_QUERY_FIELDS[field])
            else:
                value = it["properties"].get(field)
                if value is None:
                    value = it.get(field, "n/a")

            if value is not None:
                table_data[field].append(value)

    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers="keys"))
    typer.echo("\n")


def show_orders_tabulated(orders: List[Dict[str, Any]]):
    fields = ["orderId", "orderDate", "expirationDate", "orderStatus"]
    table_data = []
    for i, order in enumerate(orders):
        cur = [i + 1]
        cur.extend(order[field] for field in fields)
        granules = [o["granuleId"] for o in order["items"]]
        cur.append("\n".join(granules))  # type: ignore
        table_data.append(cur)

    headers = ["#", *fields, "STAC ids"]
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers=headers))


def show_order_review_tabulated(order_review: Dict[str, Any]):
    order_summary = order_review["orderDetails"]["summary"]
    typer.secho("summary:\n", bold=True)
    table_data = [
        ("field", "value"),
        ("authorized", order_review["authorized"]),
        ("subtotal", order_summary["subtotal"]),
        ("total", order_summary["total"]),
    ]
    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers="firstrow"))

    typer.secho("\n\nby_line_item:\n", bold=True)
    line_items = order_review["orderDetails"]["lineItems"]

    line_item_table = []
    for li in line_items:
        cur = (li["granuleId"], li["order"]["finalListPrice"])
        line_item_table.append(cur)

    typer.echo(tabulate(line_item_table, tablefmt="fancy_grid", headers=["STAC id", "cost"]))

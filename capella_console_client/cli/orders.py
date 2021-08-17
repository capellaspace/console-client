from typing import List, Dict, Any
from uuid import UUID
import typer
import questionary
from pathlib import Path

from tabulate import tabulate

from capella_console_client.cli.config import (
    CLI_SUPPORTED_RESULT_HEADERS,
    CURRENT_SETTINGS,
)
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.visualize import (
    show_orders_tabulated,
    show_order_review_tabulated,
)
from capella_console_client.cli.validate import _no_selection_bye
from capella_console_client.cli.user_searches.core import _load_and_prompt

app = typer.Typer(help="explore order history")


class PostOrderListActions(str, BaseEnum):
    reorder = "reorder"
    quit = "quit"


def _prompt_post_order_list_actions(orders: List[Dict[str, Any]]):
    choices = list(PostOrderListActions)

    action_selection = None
    while action_selection != PostOrderListActions.quit:
        action_selection = questionary.select(
            "Anything you'd like to do now?",
            choices=choices,
        ).ask()
        _no_selection_bye(action_selection)

        if action_selection == PostOrderListActions.reorder:
            order_id_choices = [order["orderId"] for order in orders]
            selected_order_id = questionary.autocomplete(
                "Specify the orderId you'd like to resubmit:",
                choices=order_id_choices,
                validate=lambda x: x in order_id_choices,
            ).ask()
            _no_selection_bye(selected_order_id)

            idx = order_id_choices.index(selected_order_id)
            stac_ids = [item["granuleId"] for item in orders[idx]["items"]]
            order_id = CLIENT.submit_order(stac_ids=stac_ids)
            typer.echo(f"Issue")
            typer.secho(
                f"\tcapella-console-wizard download --order-id {order_id}", bold=True
            )
            typer.echo("\nin order to download all products of the order.")


@app.command("list")
def list_orders(
    is_active: bool = typer.Option(
        False, "--active", help="only show active (non-expired) orders"
    ),
    limit: int = typer.Option(
        CURRENT_SETTINGS["order_list_limit"],
        help="limit orders to display (up to 300 currently)",
    ),
):
    """
    list your orders by orderDate
    """
    orders = CLIENT.list_orders(is_active=is_active)
    if not orders:
        typer.echo("Currently no orders available")
        return

    orders = sorted(orders, key=lambda x: x["orderDate"], reverse=True)[:limit]
    show_orders_tabulated(orders)
    _prompt_post_order_list_actions(orders)


@app.command("review")
def review():
    """
    review order from saved search
    """
    my_searches, selection = _load_and_prompt(
        "Which saved search would you like to use?", multiple=False
    )
    order_review = CLIENT.review_order(stac_ids=my_searches[selection]["data"])
    show_order_review_tabulated(order_review)


@app.command("reorder")
def reorder(order_id: UUID):
    """
    re-order by order ID
    """
    order = CLIENT.list_orders(str(order_id))[0]
    stac_ids = [item["granuleId"] for item in order["items"]]
    CLIENT.submit_order(stac_ids=stac_ids)

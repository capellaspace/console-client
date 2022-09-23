from typing import List, Dict, Any
from uuid import UUID
import typer
import questionary

from capella_console_client.cli.config import (
    CURRENT_SETTINGS,
)
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.visualize import (
    show_orders_tabulated,
    show_order_review_tabulated,
)
from capella_console_client.cli.validate import _no_selection_bye
from capella_console_client.cli.user_searches.core import _load_and_prompt, SearchEntity
from capella_console_client.cli.info import download_hint

app = typer.Typer(help="explore order history")


class PostOrderListActions(str, BaseEnum):
    reorder = "reorder"
    quit = "quit"

    @classmethod
    def _select_order(cls, question, orders):
        order_id_choices = [order["orderId"] for order in orders]
        selected_order_id = questionary.autocomplete(
            question,
            choices=order_id_choices,
            validate=lambda x: x in order_id_choices,
        ).ask()
        _no_selection_bye(selected_order_id)

        idx = order_id_choices.index(selected_order_id)
        return orders[idx]

    @classmethod
    def prompt_and_reorder(cls, orders):
        selected_order = cls._select_order(question="Specify the orderId you'd like to resubmit:", orders=orders)

        stac_ids = [item["granuleId"] for item in selected_order["items"]]
        order_id = CLIENT.submit_order(stac_ids=stac_ids)
        download_hint(order_id)
        return order_id


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
            PostOrderListActions.prompt_and_reorder(orders)


def _list_orders_and_tabulate(
    is_active: bool, limit: int = CURRENT_SETTINGS["order_list_limit"]
) -> List[Dict[str, Any]]:
    orders = CLIENT.list_orders(is_active=is_active)
    if not orders:
        typer.echo("Currently no orders available")
        raise typer.Exit(0)

    orders = sorted(orders, key=lambda x: x["orderDate"], reverse=True)[:limit]
    show_orders_tabulated(orders)
    return orders


@app.command("list")
def list_orders(
    is_active: bool = typer.Option(False, "--active", help="only show active (non-expired) orders"),
    limit: int = typer.Option(
        CURRENT_SETTINGS["order_list_limit"],
        help="limit orders to display (up to 300 currently)",
    ),
):
    """
    list your orders by orderDate
    """
    orders = _list_orders_and_tabulate(is_active, limit)
    _prompt_post_order_list_actions(orders)


@app.command("review")
def review(
    is_active: bool = typer.Option(False, "--active", help="only show active (non-expired) orders"),
    from_saved: bool = typer.Option(False, "--from-saved", help="from previously saved search result"),
):
    """
    review orders
    """
    if from_saved:
        my_searches, selection = _load_and_prompt(
            "Which saved search result would you like to use?",
            search_entity=SearchEntity.result,
            multiple=False,
        )
        stac_ids = my_searches[selection]["data"]  # type: ignore
    else:
        orders = _list_orders_and_tabulate(is_active)
        selected_order = PostOrderListActions._select_order(
            question="Which order would you like to review:", orders=orders
        )
        stac_ids = [item["granuleId"] for item in selected_order["items"]]

    order_review = CLIENT.review_order(stac_ids=stac_ids)
    show_order_review_tabulated(order_review)


@app.command("reorder")
def reorder(order_id: UUID):
    """
    re-order by order ID
    """
    order = CLIENT.list_orders(str(order_id))[0]
    stac_ids = [item["granuleId"] for item in order["items"]]
    new_order_id = CLIENT.submit_order(stac_ids=stac_ids)
    download_hint(new_order_id)

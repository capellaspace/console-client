import typer
import questionary
from questionary import prompt

from capella_console_client.enumerations import ProductType
from capella_console_client.cli.user_searches.core import _load_and_prompt, SearchEntity
from capella_console_client.cli.config import CURRENT_SETTINGS
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import _validate_uuid, _validate_dir_exists
from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.search import (
    _prompt_search_filters,
    search_and_post_actions,
)
from capella_console_client.cli.orders import (
    _list_orders_and_tabulate,
    PostOrderListActions,
)


app = typer.Typer(help="order and download products")


class CheckoutStartOptions(str, BaseEnum):
    new_search = "new search"
    saved_search = "use previously saved search results"
    collect_id = "provide a collect id"
    tasking_request_id = "provide a taskingrequest id"
    existing_order = "select existing order"

    @classmethod
    def _get_choices(cls):
        return list(CheckoutStartOptions)


def interactive_search_order_and_download():

    start_from_opt = questionary.select("What would you like to do?", choices=CheckoutStartOptions._get_choices()).ask()

    questions = _get_questions(start_from_opt)
    if start_from_opt in [
        CheckoutStartOptions.collect_id,
        CheckoutStartOptions.tasking_request_id,
    ]:
        answers = prompt(questions)
        if answers["include"] == "all":
            del answers["include"]
        paths = CLIENT.download_products(**answers)

    elif start_from_opt in (
        CheckoutStartOptions.new_search,
        CheckoutStartOptions.saved_search,
    ):
        if start_from_opt == CheckoutStartOptions.new_search:
            search_query = _prompt_search_filters()
            stac_items = search_and_post_actions(search_query)
            answers = prompt(questions)
            order_id = CLIENT.submit_order(
                items=stac_items,
                check_active_orders=True,
                omit_search=True,
            )
            stac_ids = [s["id"] for s in stac_items]

        else:
            stac_ids = _stac_ids_from_saved_search()
            answers = prompt(questions)
            order_id = CLIENT.submit_order(
                stac_ids=stac_ids,
                check_active_orders=True,
                omit_search=True,
            )

        items_presigned = CLIENT.get_presigned_items(order_id, stac_ids=stac_ids)
        paths = CLIENT.download_products(items_presigned=items_presigned, **answers)
    elif start_from_opt == CheckoutStartOptions.existing_order:
        orders = _list_orders_and_tabulate(is_active=False, limit=300)
        order_id = PostOrderListActions.prompt_and_reorder(orders)
        answers = prompt(questions)
        paths = CLIENT.download_products(**answers, order_id=order_id)

    product_paths = set()
    for stac_id in paths:
        asset_paths = list(paths[stac_id].values())
        product_paths.update([a.parent for a in asset_paths])

    if questionary.confirm("Do you want to open any product directories?").ask():
        dirs_to_open = questionary.checkbox(
            "select which product directories you want to open",
            choices=list(map(str, product_paths)),
        ).ask()

        for open_dir in dirs_to_open:
            typer.launch(open_dir)


def _get_questions(start_option: CheckoutStartOptions):
    question_types = {
        "uuid": {
            "type": "text",
            "name": start_option.name,
            "message": f"{start_option.value}:",
            "validate": _validate_uuid,
        },
        "product_types": {
            "type": "checkbox",
            "name": "product_types",
            "message": "product type(s):",
            "choices": list(ProductType),
        },
        "asset_types": {
            "type": "checkbox",
            "name": "include",
            "message": "asset type:",
            "choices": ["all", "raster", "metadata", "thumbnail"],
        },
        "local_dir": {
            "type": "path",
            "name": "local_dir",
            "message": "download location:",
            "default": CURRENT_SETTINGS["out_path"],
            "validate": _validate_dir_exists,
        },
    }

    return {
        CheckoutStartOptions.collect_id: [
            question_types["uuid"],
            question_types["product_types"],
            question_types["asset_types"],
            question_types["local_dir"],
        ],
        CheckoutStartOptions.tasking_request_id: [
            question_types["uuid"],
            question_types["product_types"],
            question_types["asset_types"],
            question_types["local_dir"],
        ],
        CheckoutStartOptions.existing_order: [
            question_types["asset_types"],
            question_types["local_dir"],
        ],
        CheckoutStartOptions.new_search: [
            question_types["asset_types"],
            question_types["local_dir"],
        ],
        CheckoutStartOptions.saved_search: [
            question_types["asset_types"],
            question_types["local_dir"],
        ],
    }[start_option]


def _stac_ids_from_saved_search():
    saved, selection = _load_and_prompt(
        "Which saved search would you like to use?",
        search_entity=SearchEntity.result,
        multiple=False,
    )
    stac_ids = saved[selection]["data"]
    return stac_ids

from collections import defaultdict
from typing import List, Dict, Any

import typer
import questionary
from tabulate import tabulate


from capella_console_client.config import (
    TYPE_BY_FIELD_NAME,
    STAC_PREFIXED_BY_QUERY_FIELDS,
    SUPPORTED_SEARCH_FIELDS,
)
from capella_console_client.validate import get_validator
from capella_console_client.cli.cache import CLICachePaths
from capella_console_client.cli.config import (
    DEFAULT_SEARCH_RESULT_FIELDS,
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
    PROMPT_OPERATORS,
)


def prompt_search_operator(field):
    operators = questionary.checkbox(
        f"{field}:", choices=["=", "in", ">", ">=", "<", "<="]
    ).ask()

    ops_map = {
        "=": "eq",
        ">": "gt",
        ">=": "gte",
        "<": "lt",
        "<=": "lte",
        "in": "in",
    }

    return [ops_map[o] for o in operators]


def prompt_search_filter() -> Dict[str, Any]:
    search_filter_names = questionary.checkbox(
        "Which filters?", choices=CLI_SUPPORTED_SEARCH_FILTERS
    ).ask()

    search_kwargs = {"limit": CURRENT_SETTINGS["limit"]}

    # TODO: validation, switches
    for key in search_filter_names:
        search_op = None
        if key in PROMPT_OPERATORS:
            search_op = prompt_search_operator(key)

        target_type = TYPE_BY_FIELD_NAME.get(key, str)
        str_val = questionary.text(
            message=f"{key}:",
            validate=get_validator(target_type),
        ).ask()

        if target_type:
            search_kwargs[key] = target_type(str_val)

    return search_kwargs


def show_tabulated(stac_items: List[Dict[str, Any]]):
    try:
        fields = CLICachePaths.load_search_result_fields()
    except:
        fields = DEFAULT_SEARCH_RESULT_FIELDS

    table_data = defaultdict(list)

    for field in fields:
        for it in stac_items:
            if field in STAC_PREFIXED_BY_QUERY_FIELDS:
                value = it["properties"].get(STAC_PREFIXED_BY_QUERY_FIELDS[field])
            else:
                value = it.get(field, "n/a")

            if value is not None:
                table_data[field].append(value)

    typer.echo(tabulate(table_data, tablefmt="fancy_grid", headers="keys"))
    print("\n")

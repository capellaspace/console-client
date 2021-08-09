from collections import defaultdict
from typing import List, Dict, Any

import typer
import questionary
from tabulate import tabulate


from capella_console_client.config import (
    STAC_PREFIXED_BY_QUERY_FIELDS,
    SUPPORTED_SEARCH_FIELDS,
)
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import get_validator, get_caster
from capella_console_client.cli.cache import CLICachePaths
from capella_console_client.cli.config import (
    DEFAULT_SEARCH_RESULT_FIELDS,
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
    PROMPT_OPERATORS
)

app = typer.Typer(callback=None)


# TODO: autocomplete option
@app.command()
def interactive():
    search_kwargs = prompt_search_filter()
    stac_items = CLIENT.search(**search_kwargs)
    show_tabulated(stac_items)


def prompt_search_operator(field) -> Dict[str, str]:
    if field not in PROMPT_OPERATORS:
        return [None]
    
    operators = questionary.checkbox(
        f"{field}:", choices=["=", ">", ">=", "<", "<=", "in"]
    ).ask()

    ops_map = {
        "=": "eq",
        ">": "gt",
        ">=": "gte",
        "<": "lt",
        "<=": "lte",
        "in": "in",
    }

    return {o: ops_map[o] for o in operators}


def prompt_search_filter() -> Dict[str, Any]:
    search_filter_names = questionary.checkbox(
        "What are you looking for today?", choices=CLI_SUPPORTED_SEARCH_FILTERS
    ).ask()

    search_kwargs = {"limit": CURRENT_SETTINGS["limit"]}

    # TODO: validation, switches
    for field in search_filter_names:
        search_ops = prompt_search_operator(field)

        for search_op in search_ops:
            suffix = f"[{search_op}]" if search_op is not None else ""
            str_val = questionary.text(
                message=f"{field} {suffix}:",
                validate=get_validator(field),
            ).ask()

            # optional cast from str
            cast_fct = get_caster(field)
            if cast_fct:
                field_desc = f"{field}__{search_ops[search_op]}" if search_op else field
                search_kwargs[field_desc] = cast_fct(str_val)

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

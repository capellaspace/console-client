import os
from collections import defaultdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import typer
import questionary
from tabulate import tabulate

from capella_console_client.enumerations import BaseEnum
from capella_console_client.config import (
    STAC_PREFIXED_BY_QUERY_FIELDS,
    SUPPORTED_SEARCH_FIELDS,
)
from capella_console_client.enumerations import (
    InstrumentMode,
    ProductClass,
    ObservationDirection,
    OrbitState,
    OrbitalPlane,
    ProductType,
)
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import get_validator, get_caster, _validate_out_path
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    DEFAULT_SEARCH_RESULT_FIELDS,
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
    PROMPT_OPERATORS,
)

app = typer.Typer(help='search STAC items')


# TODO: autocomplete option
@app.command()
def interactive():
    """
    interactive search with prompts
    """
    search_kwargs = _prompt_search_filter()
    stac_items = CLIENT.search(**search_kwargs)

    if stac_items:
        show_tabulated(stac_items)
        _prompt_post_search_actions(stac_items)


def _prompt_search_operator(field: str) -> Dict[str, str]:
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


def prompt_enum_choices(field: str) -> Optional[Dict[str, Any]]:
    enum_cls = {
        "instrument_mode": InstrumentMode,
        "observation_direction": ObservationDirection,
        "orbital_plane": OrbitalPlane,
        "orbit_state": OrbitState,
        "product_category": ProductClass,
        "product_type": ProductType,
    }.get(field)

    if not enum_cls:
        return None

    choices = questionary.checkbox(
        f"{field}:", choices=[e.value for e in enum_cls]
    ).ask()
    return {f"{field}__in": choices}


def _prompt_search_filter() -> Dict[str, Any]:
    search_filter_names = questionary.checkbox(
        "What are you looking for today?", choices=CLI_SUPPORTED_SEARCH_FILTERS
    ).ask()

    if not search_filter_names:
        typer.echo("Please provide at least one search condition")
        raise typer.Exit()

    search_kwargs = {"limit": CURRENT_SETTINGS["limit"]}

    for field in search_filter_names:
        cur_search_payload = prompt_enum_choices(field)

        # enum takes precedence
        if cur_search_payload:
            search_kwargs.update(cur_search_payload)
            continue

        search_ops = _prompt_search_operator(field)

        for search_op in search_ops:
            suffix = f"[{search_op}]" if search_op is not None else ""
            str_val = questionary.text(
                message=f"{field} {suffix}:",
                validate=get_validator(field),
            ).ask()

            # optional cast from str
            cast_fct = get_caster(field)
            field_desc = f"{field}__{search_ops[search_op]}" if search_op else field
            if cast_fct:
                search_kwargs[field_desc] = cast_fct(str_val)
            else:
                search_kwargs[field_desc] = str_val

    return search_kwargs


def show_tabulated(stac_items: List[Dict[str, Any]]):
    fields = CURRENT_SETTINGS["search_fields"]
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



class PostSearchActions(str, BaseEnum):
    save_my_searches = "save into 'my-searches'",
    export_json = "export as .json"
    

def _get_default_search_results_name():
    dt_format = "%Y%m%dT%H%M%S"
    ts = datetime.strftime(datetime.utcnow(), dt_format) 
    return f"search_results_{ts}"

def _prompt_post_search_actions(stac_items: List[Dict[str, Any]]):

    action_selection = questionary.checkbox(
        f"Anything you'd like to do with these {len(stac_items)} STAC items?", 
        choices=list(PostSearchActions)
    ).ask()

    if PostSearchActions.save_my_searches in action_selection:
        identifier = questionary.text(
            message="Please provide an identifier for your search",
            default=_get_default_search_results_name(),
            validate=lambda x: x is not None and len(x) > 0
        ).ask()
        typer.echo(f"Adding '{identifier}' to my-searches")
        stac_ids = [i['id'] for i in stac_items]
        CLICache.update_my_searches(identifier, stac_ids)

    
    if PostSearchActions.export_json in action_selection:
        default = CURRENT_SETTINGS['out_path']
        if default[-1] != os.sep:
            default += os.sep
        default += f'{_get_default_search_results_name()}.json'
        
        path = questionary.path(
            message="Please provide path and filename where you want to save the stac items .json",
            default=default,
            validate=_validate_out_path
        ).ask()

        if path:
            with open(path, 'w') as fp:
                json.dump(stac_items, fp)
            typer.echo(f"Saved {len(stac_items)} STAC items to {path}")
        
            if questionary.confirm("Would you like to open it?").ask():
                os.system(f'open {path}')

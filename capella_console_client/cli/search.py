import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import typer
import questionary
from tabulate import tabulate

from capella_console_client.enumerations import BaseEnum
from capella_console_client.config import (
    STAC_PREFIXED_BY_QUERY_FIELDS,
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
from capella_console_client.cli.validate import (
    get_validator,
    get_caster,
    _validate_out_path,
)
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
    PROMPT_OPERATORS,
)
from capella_console_client.cli.my_searches import _load_and_prompt
from capella_console_client.cli.visualize import show_tabulated
from capella_console_client.cli.settings import _prompt_search_result_headers


app = typer.Typer(help="search STAC items")


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

    if not operators:
        typer.echo("Please select at least one search operator")
        raise typer.Exit(code=1)

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
        typer.echo("Please select at least one search condition")
        raise typer.Exit(code=1)

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


class PostSearchActions(str, BaseEnum):
    adjust_headers = "adjust result table headers and re-print"
    save_my_searches = ("save into 'my-searches'",)
    export_json = "export as .json"
    quit = "quit"

    @classmethod
    def save_search(cls, stac_items: Dict[str, Any]):
        identifier = questionary.text(
            message="Please provide an identifier for your search",
            default=_get_default_search_results_name(),
            validate=lambda x: x is not None and len(x) > 0,
        ).ask()
        typer.echo(f"Adding '{identifier}' to my-searches")
        stac_ids = [i["id"] for i in stac_items]
        CLICache.update_my_searches(identifier, stac_ids)

    @classmethod
    def export_search(cls, stac_items: Dict[str, Any]) -> str:
        default = CURRENT_SETTINGS["out_path"]
        if default[-1] != os.sep:
            default += os.sep
        default += f"{_get_default_search_results_name()}.json"

        path = questionary.path(
            message="Please provide path and filename where you want to save the stac items .json",
            default=default,
            validate=_validate_out_path,
        ).ask()
        if not path:
            raise typer.Exit()

        with open(path, "w") as fp:
            json.dump(stac_items, fp)
        typer.echo(f"Saved {len(stac_items)} STAC items to {path}")
        return path


def _get_default_search_results_name():
    dt_format = "%Y%m%dT%H%M%S"
    ts = datetime.strftime(datetime.utcnow(), dt_format)
    return f"search_results_{ts}"


def _prompt_post_search_actions(stac_items: List[Dict[str, Any]], no_save=False):
    choices = list(PostSearchActions)
    if no_save:
        del choices[choices.index(PostSearchActions.save_my_searches)]

    action_selection = None
    while action_selection != PostSearchActions.quit:
        action_selection = questionary.select(
            "Anything you'd like to do now?",
            choices=choices,
        ).ask()

        if not action_selection:
            typer.echo("nothing selected ... bye")
            raise typer.Exit(code=1)

        if action_selection == PostSearchActions.adjust_headers:
            search_headers = _prompt_search_result_headers()
            CURRENT_SETTINGS["search_headers"] = search_headers
            show_tabulated(stac_items, search_headers)

        if action_selection == PostSearchActions.save_my_searches:
            PostSearchActions.save_search(stac_items)

        if action_selection == PostSearchActions.export_json:
            path = PostSearchActions.export_search(stac_items)
            if questionary.confirm("Would you like to open it?").ask():
                os.system(f"open {path}")


@app.command()
def from_saved():
    """
    select and show STAC items of saved search
    """
    my_searches, selection = _load_and_prompt(
        "Which saved search would you like to use?", multiple=False
    )
    stac_items = CLIENT.search(ids=my_searches[selection])

    if stac_items:
        show_tabulated(stac_items)
        _prompt_post_search_actions(stac_items, no_save=True)

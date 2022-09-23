import os
from typing import List, Dict, Any, Optional, Tuple
import json
from collections import defaultdict

import typer
import questionary

from capella_console_client.enumerations import BaseEnum
from capella_console_client.search import SearchResult
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import (
    get_validator,
    get_caster,
    _validate_out_path,
    _no_selection_bye,
    _at_least_one_selected,
)
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.config import (
    CLI_SUPPORTED_SEARCH_FILTERS,
    CURRENT_SETTINGS,
    PROMPT_OPERATORS,
    ENUM_CHOICES_BY_FIELD_NAME,
)
from capella_console_client.cli.user_searches.my_search_results import _load_and_prompt
from capella_console_client.cli.user_searches.core import SearchEntity
from capella_console_client.cli.visualize import show_tabulated
from capella_console_client.cli.settings import _prompt_search_result_headers
from capella_console_client.cli.info import my_search_entity_info
from capella_console_client.cli.prompt_helpers import get_first_checked


# TODO: autocomplete option
def interactive_search():
    search_query = _prompt_search_filters()
    choices = list(PostSearchActions)
    del choices[choices.index(PostSearchActions.continue_flow)]
    search_and_post_actions(search_query, choices=choices)


class STACQueryPayload(dict):
    OPS_MAP = {
        "=": "eq",
        ">": "gt",
        ">=": "gte",
        "<": "lt",
        "<=": "lte",
        "in": "in",
    }

    REV_OPS_MAP = {
        "eq": "=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "in": "in",
    }

    def __str__(self):
        _filters = []
        for k, v in self.items():
            if isinstance(v, list):
                cur = f"{k}{'|'.join(map(str, v))}"
            else:
                cur = f"{k}{v}"
            _filters.append(cur)

        return "-".join(_filters)

    @classmethod
    def unflatten(cls, other) -> "STACQueryPayload":
        _con = defaultdict(list)
        for k, v in other.items():
            if "__" in k:
                key, op = k.split("__")
                op = STACQueryPayload.REV_OPS_MAP[op]
                _con[key].append((op, v))
            else:
                _con[k].append(("=", v))
        return cls(_con)

    def flatten(self, other):
        _con = {}
        for field, op_val_tuples in other.items():
            for op, val in op_val_tuples:
                _con.add(field, op, val)
        return _con

    def add(self, field: str, search_op: str, value: Any):
        if not search_op or search_op == "=":
            field_desc = field
        else:
            field_desc = f"{field}__{self.OPS_MAP[search_op]}"
        self[field_desc] = value


def _prompt_search_operator(field: str, prev_selection: List[str]) -> List[str]:
    choices = [questionary.Choice(cur, checked=cur in prev_selection) for cur in STACQueryPayload.OPS_MAP.keys()]
    operators = questionary.checkbox(
        f"{field}:",
        choices=choices,
        initial_choice=get_first_checked(choices, prev_selection),
    ).ask()
    _no_selection_bye(operators, "Please select at least one search operator")
    return operators


def _prompt_enum_choices(field: str, init: Any = None) -> Optional[Dict[str, Any]]:
    if init is None:
        init = []

    if field not in ENUM_CHOICES_BY_FIELD_NAME:
        return None

    choices = [  # type: ignore
        questionary.Choice(e.value, checked=e.value in init) for e in ENUM_CHOICES_BY_FIELD_NAME[field]
    ]

    choices = questionary.checkbox(
        f"{field}:", choices=choices, initial_choice=get_first_checked(choices, init)
    ).ask()  # type: ignore
    _no_selection_bye(choices)
    return {field: choices}


def _prompt_operator_value(field: str, search_op: str, init: Any = ""):
    suffix = f"[{search_op}]" if search_op else ""
    str_val = questionary.text(
        message=f"{field} {suffix}:",
        default=str(init),
        validate=get_validator(field),
    ).ask()
    _no_selection_bye(str_val)
    cast_fct = get_caster(field)
    if cast_fct:
        return cast_fct(str_val)
    return str_val


def _prompt_search_filters(prev_search: STACQueryPayload = None) -> STACQueryPayload:
    if prev_search is None:
        prev_search = STACQueryPayload()

    choices = [questionary.Choice(cur, checked=cur in prev_search) for cur in CLI_SUPPORTED_SEARCH_FILTERS]

    search_filter_names = questionary.checkbox(
        "Select your search filters:",
        choices=choices,
        initial_choice=get_first_checked(choices, prev_search),
        validate=_at_least_one_selected,
    ).ask()
    _no_selection_bye(search_filter_names, "Please select at least one search filter")

    query = STACQueryPayload()
    for field in search_filter_names:
        prev_selected_ops = {x[0]: x[1] for x in prev_search.get(field, [])}
        cur = _prompt_enum_choices(field, init=prev_selected_ops.get("="))

        # enum takes precedence
        if cur:
            query.update(cur)
            continue

        if field in PROMPT_OPERATORS:
            operators = _prompt_search_operator(field, list(prev_selected_ops.keys()))
        else:
            operators = ["="]

        for search_op in operators:
            init = prev_selected_ops.get(search_op, "")
            value = _prompt_operator_value(field, search_op, init)
            query.add(field, search_op, value)

    if "limit" not in query:
        query["limit"] = CURRENT_SETTINGS["limit"]

    if "constellation" not in query:
        query["constellation"] = "capella"

    return query


class PostSearchActions(str, BaseEnum):
    refine_search = "refine search"
    adjust_headers = "change result table headers"
    save_current_search = "save search query and result into my-search-results | my-search-queries"
    export_json = "export STAC items of search as .json"
    continue_flow = "continue"
    quit = "quit"

    @classmethod
    def save_search(cls, result: SearchResult, search_kwargs: STACQueryPayload):
        identifier = questionary.text(
            message="Please provide an identifier for your search:",
            default=str(search_kwargs),
            validate=lambda x: x is not None and len(x) > 0,
        ).ask()
        CLICache.update_my_search_results(identifier, result.stac_ids, is_new=True)
        CLICache.update_my_search_queries(identifier, search_kwargs, is_new=True)  # type: ignore
        my_search_entity_info(identifier)

    @classmethod
    def export_search(cls, result: SearchResult, search_kwargs: STACQueryPayload) -> str:
        default = CURRENT_SETTINGS["out_path"]
        if default[-1] != os.sep:
            default += os.sep
        default += f"{search_kwargs}.json"

        path = questionary.path(
            message="Please provide path and filename where you want to save the stac items .json",
            default=default,
            validate=_validate_out_path,
        ).ask()
        _no_selection_bye(path, "Please provide a path")

        with open(path, "w") as fp:
            json.dump(result, fp)
        typer.echo(f"Saved {len(result)} STAC items to {path}")
        return path

    @classmethod
    def refine_search_cmd(cls, prev_search: STACQueryPayload) -> Tuple[STACQueryPayload, SearchResult]:
        prev_search.pop("constellation", None)
        if prev_search["limit"][0][1] == CURRENT_SETTINGS["limit"]:
            prev_search.pop("limit")

        typer.echo(f"Refining\n\t{json.dumps(prev_search)}")
        search_query = _prompt_search_filters(prev_search=prev_search)
        stac_items = CLIENT.search(**search_query)
        return (search_query, stac_items)

    @classmethod
    def _get_choices(cls, results_found: bool) -> List["PostSearchActions"]:
        if results_found:
            return list(PostSearchActions)
        else:
            return [PostSearchActions.refine_search, PostSearchActions.quit]


def search_and_post_actions(search_query: STACQueryPayload, choices: List[PostSearchActions] = None):
    result = CLIENT.search(**search_query)
    if result:
        show_tabulated(result, show_row_number=True)

    result = _prompt_post_search_actions(result, search_query, choices)
    return result


def _prompt_post_search_actions(
    result: SearchResult,
    search_kwargs: STACQueryPayload,
    choices: List[PostSearchActions] = None,
):
    if not choices:
        choices = PostSearchActions._get_choices(results_found=len(result) > 0)
    action_selection = None

    while action_selection != PostSearchActions.quit:
        action_selection = questionary.select(
            "Anything you'd like to do now?",
            choices=choices,
        ).ask()
        _no_selection_bye(action_selection)

        if action_selection == PostSearchActions.adjust_headers:
            search_headers = _prompt_search_result_headers()
            CURRENT_SETTINGS["search_headers"] = search_headers
            CLICache.write_user_settings("search_headers", search_headers)
            show_tabulated(result, search_headers, show_row_number=True)

        if action_selection == PostSearchActions.save_current_search:
            PostSearchActions.save_search(result, search_kwargs)
            del choices[choices.index(PostSearchActions.save_current_search)]

        if action_selection == PostSearchActions.export_json:
            path = PostSearchActions.export_search(result, search_kwargs)
            if questionary.confirm("Would you like to open it?").ask():
                os.system(f"open {path}")

        if action_selection == PostSearchActions.refine_search:
            prev_search = STACQueryPayload.unflatten(search_kwargs)
            search_kwargs, result = PostSearchActions.refine_search_cmd(prev_search)
            show_tabulated(result, show_row_number=True)
            choices = PostSearchActions._get_choices(results_found=bool(result))

        if action_selection == PostSearchActions.continue_flow:
            return result


def from_saved():
    """
    select and show STAC items of saved search
    """
    entity = questionary.select(
        "Would you like to use a saved query or a saved result",
        choices=[SearchEntity.query.name, SearchEntity.result.name],
    ).ask()
    _no_selection_bye(entity)

    search_entity = SearchEntity[entity]
    saved, selection = _load_and_prompt(
        f"Which saved {entity} would you like to use?",
        search_entity=search_entity,
        multiple=False,
    )

    if search_entity == SearchEntity.result:
        search_query = dict(ids=saved[selection]["data"])
    else:
        search_query = saved[selection]["data"]

    search_and_post_actions(search_query)

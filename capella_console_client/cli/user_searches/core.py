from typing import Tuple, Dict, Any, List
from datetime import datetime

import typer
import questionary

from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.validate import _no_selection_bye
from capella_console_client.cli.cache import CLICache
from capella_console_client.cli.info import no_data_info


class SearchEntity(str, BaseEnum):
    result = 1
    query = 2


def _get_load_fct(search_entity: SearchEntity):
    return {
        SearchEntity.result: CLICache.load_my_search_results,
        SearchEntity.query: CLICache.load_my_search_queries,
    }[search_entity]


def _get_write_fct(search_entity):
    return {
        SearchEntity.result: CLICache.write_my_search_results,
        SearchEntity.query: CLICache.write_my_search_queries,
    }[search_entity]


def _load_and_prompt(
    question: str,
    search_entity: SearchEntity,
    multiple: bool = True,
) -> Tuple[Dict[str, Any], List[str]]:

    saved = _get_load_fct(search_entity)()

    if not saved:
        no_data_info(search_entity)

    typer.echo("\n\n")

    question_cls = questionary.checkbox if multiple else questionary.select
    selection = question_cls(message=question, choices=saved).ask()  # type: ignore
    _no_selection_bye(selection)
    return (saved, selection)


def rename_search_entity(search_entity: SearchEntity):
    saved, selection = _load_and_prompt(f"Which saved {search_entity.name} would you like to rename?", search_entity)

    change_cnt = 0
    for selected in selection:
        new_name = questionary.text(
            message=f"Rename {selected} to:",
            default=selected,
            validate=lambda x: x is not None and len(x) > 0,
        ).ask()

        if new_name != selected:
            val = saved[selected]
            saved[new_name] = val
            saved[new_name]["updated_at"] = str(datetime.now())[:-7]
            del saved[selected]
            change_cnt += 1

    if change_cnt > 0:
        _get_write_fct(search_entity)(saved)
        typer.echo(f"Renamed {change_cnt} search {search_entity.name}")

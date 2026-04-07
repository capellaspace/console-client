from typing import Any

import questionary
import typer
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.validate import _validate_uuid
from capella_console_client.cli.visualize import show_cancel_result_tabulated, show_update_result_tabulated
from capella_console_client.enumerations import BaseEnum, ProductType


def get_first_checked(choices: list[questionary.Choice], prev_search=None) -> questionary.Choice:
    first_checked = choices[0]
    if prev_search:
        first_checked = next(c for c in choices if c.checked)
    return first_checked


def _validate_request_ids(text: str) -> bool | str:
    """
    Validate comma-separated request IDs (UUIDs).
    Returns True if valid, error message string if invalid.
    """
    if not text or not text.strip():
        return "At least one request ID is required"

    ids = [id_.strip() for id_ in text.split(",")]

    for id_ in ids:
        result = _validate_uuid(id_)
        if result is not True:
            return f"Invalid UUID '{id_}': {result}"

    return True


def _fetch_users() -> list[dict[str, Any]]:
    users = []
    page_cnt = 1

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        resp = CLIENT._sesh.get(f"/users/?limit=1000&page={page_cnt}")
        page = resp.json()
        total_pages = page["totalPages"]

        task = progress.add_task("[cyan]Fetching users...", total=total_pages)

        users.extend(page["results"])
        progress.update(task, advance=1)

        if page["currentPage"] == page["totalPages"]:
            return users

        page_cnt += 1

        while page_cnt <= total_pages:
            resp = CLIENT._sesh.get(f"/users/?limit=1000&page={page_cnt}")
            page = resp.json()
            users.extend(page["results"])
            progress.update(task, advance=1)

            if page["currentPage"] == page["totalPages"]:
                break

            page_cnt += 1

    return users


def _fetch_orgs() -> list[dict[str, Any]]:
    orgs = []
    page_cnt = 1

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        resp = CLIENT._sesh.get(f"/organizations/?limit=5000&page={page_cnt}&fields=id,name")
        page = resp.json()
        total_pages = page["totalPages"]

        task = progress.add_task("[cyan]Fetching organizations...", total=total_pages)

        orgs.extend(page["results"])
        progress.update(task, advance=1)

        if page["currentPage"] == page["totalPages"]:
            return orgs

        page_cnt += 1

        while page_cnt <= total_pages:
            resp = CLIENT._sesh.get(f"/organizations/?limit=5000&page={page_cnt}&fields=id,email")
            page = resp.json()
            orgs.extend(page["results"])
            progress.update(task, advance=1)

            if page["currentPage"] == page["totalPages"]:
                break

            page_cnt += 1

    return orgs


def _prompt_admin_target() -> tuple[str | None, str | None]:
    admin_for_who = questionary.select(
        "for who:",
        choices=["user", "org"],
    ).ask()

    if not admin_for_who:
        return (None, None)

    selection_method = questionary.select(
        "how to select:",
        choices=["Enter UUID manually", f"Fetch {admin_for_who} from API"],
    ).ask()

    if not selection_method:
        return (None, None)

    admin_uuid = None

    if selection_method == "Enter UUID manually":
        uuid_response = questionary.text(
            "uuid:",
            validate=_validate_uuid,
        ).ask()

        if not uuid_response:
            return (None, None)

        admin_uuid = uuid_response
    else:
        if admin_for_who == "user":
            users = _fetch_users()

            if not users:
                typer.echo("No users found")
                return (None, None)

            email_to_id = {user["email"]: user["id"] for user in users}
            email_choices = list(email_to_id.keys())

            selected_email = questionary.autocomplete(
                "Select user by email:",
                choices=email_choices,
            ).ask()

            if not selected_email:
                return (None, None)

            admin_uuid = email_to_id[selected_email]
        else:
            orgs = _fetch_orgs()

            if not orgs:
                typer.echo("No organizations found")
                return (None, None)

            name_to_id = {org["name"]: org["id"] for org in orgs}
            name_choices = list(name_to_id.keys())

            selected_name = questionary.autocomplete(
                "Select organization by name:",
                choices=name_choices,
            ).ask()

            if not selected_name:
                return (None, None)

            admin_uuid = name_to_id[selected_name]

        if not admin_uuid:
            return (None, None)

    return (admin_for_who, admin_uuid)


class ScopeOptions(str, BaseEnum):
    user = "current user"
    org = "current organization (requires elevated perms)"
    admin = "admin (requires elevated perms)"
    by_id = "by request ID"

    @classmethod
    def _get_choices(cls):
        whoami = CLIENT.whoami()
        valid = [cls.user, cls.by_id]
        if "organization-manager" in whoami["roles"]:
            valid.append(cls.org)
        if "admin" in whoami["roles"]:
            valid.append(cls.admin)
        return valid


def _prompt_selection(
    action: str,
    entity_label: str,
    search_fn,
    overview_fn,
    id_search_kwarg: str,
    base_search_kwargs: dict | None = None,
) -> list[str] | None:
    """
    Prompt for scope, search for matching items, and let the user pick via checkbox.
    Returns the selected IDs, or None if the user aborted at any step.
    """
    for_who_choices = ScopeOptions._get_choices()

    if len(for_who_choices) > 1:
        for_who = questionary.select(f"{action.capitalize()} {entity_label}s of ?", choices=for_who_choices).ask()
    else:
        for_who = ScopeOptions.user

    search_kwargs = {**(base_search_kwargs or {})}

    if for_who == ScopeOptions.org:
        search_kwargs["for_org"] = True
    elif for_who == ScopeOptions.admin:
        admin_for_who, admin_uuid = _prompt_admin_target()
        if not admin_for_who:
            return None
        if admin_for_who == "user":
            search_kwargs["user_id"] = admin_uuid
        elif admin_for_who == "org":
            search_kwargs["org_id"] = [admin_uuid]
    elif for_who == ScopeOptions.by_id:
        ids_input = questionary.text(
            f"Enter {entity_label} ID(s) (comma-separated for multiple):",
            validate=lambda text: _validate_request_ids(text),
        ).ask()
        if not ids_input:
            return None
        search_kwargs[id_search_kwarg] = [id_.strip() for id_ in ids_input.split(",")]

    items = search_fn(**search_kwargs, show_progress=True)

    if not items:
        typer.echo(f"No {action}able {entity_label}s found for {search_kwargs=}...")
        return None

    id_by_option = {
        overview_fn(item): item["properties"][id_search_kwarg.replace("_id", "Id").replace("_", "")] for item in items
    }
    selection = questionary.checkbox(f"Which {entity_label}?", choices=list(id_by_option.keys())).ask()

    if not selection:
        typer.echo("Nothing selected ... aborting")
        return None

    return [id_by_option[t] for t in selection]


_UPDATABLE_FIELD_LABELS: dict[str, str] = {
    "name": "name",
    "description": "description",
    "custom_attribute_1": "custom attribute 1",
    "custom_attribute_2": "custom attribute 2",
    "product_types": "product types",
}

UPDATABLE_PRODUCT_TYPES = [
    ProductType.SLC,
    ProductType.GEO,
    ProductType.SICD,
    ProductType.GEC,
    ProductType.SIDD,
    ProductType.CPHD,
    ProductType.CSI,
    ProductType.CSIDD,
    ProductType.VC,
]


def _prompt_update_fields() -> dict | None:
    selected_labels = questionary.checkbox(
        "Which fields to update?",
        choices=list(_UPDATABLE_FIELD_LABELS.values()),
    ).ask()

    if not selected_labels:
        return None

    label_to_kwarg = {v: k for k, v in _UPDATABLE_FIELD_LABELS.items()}
    update_kwargs: dict = {}

    for label in selected_labels:
        kwarg = label_to_kwarg[label]

        if kwarg == "product_types":
            selected = questionary.checkbox(
                "select product types:",
                choices=[pt.value for pt in UPDATABLE_PRODUCT_TYPES],
            ).ask()
            if not selected:
                return None
            update_kwargs[kwarg] = selected
        else:
            value = questionary.text(
                f"new {label}:",
                validate=lambda t: "value cannot be empty" if not t.strip() else True,
            ).ask()
            if value is None:
                return None
            update_kwargs[kwarg] = value

    return update_kwargs


def _cancel_items(
    search_fn,
    cancel_fn,
    overview_fn,
    entity_label: str,
    cancel_statuses: list[str],
    id_search_kwarg: str,
) -> None:
    item_ids = _prompt_selection(
        action="cancel",
        entity_label=entity_label,
        search_fn=search_fn,
        overview_fn=overview_fn,
        id_search_kwarg=id_search_kwarg,
        base_search_kwargs={"status": cancel_statuses},
    )
    if item_ids is None:
        return
    selection_str = "\n".join(f" - {item_id}" for item_id in item_ids)
    if questionary.confirm(
        f"Please confirm you'd like to cancel the following {entity_label}s"
        f" (cancelation charges might apply):\n\n{selection_str}\n"
    ).ask():
        show_cancel_result_tabulated(cancel_fn(*item_ids))


def _update_items(
    search_fn,
    update_fn,
    overview_fn,
    entity_label: str,
    id_search_kwarg: str,
) -> None:
    item_ids = _prompt_selection(
        action="update",
        entity_label=entity_label,
        search_fn=search_fn,
        overview_fn=overview_fn,
        id_search_kwarg=id_search_kwarg,
    )
    if item_ids is None:
        return
    update_kwargs = _prompt_update_fields()
    if not update_kwargs:
        return
    fields_str = "\n".join(f"  {_UPDATABLE_FIELD_LABELS[k]}: {v!r}" for k, v in update_kwargs.items())
    ids_str = "\n".join(f" - {item_id}" for item_id in item_ids)
    if not questionary.confirm(
        f"Apply the following updates:\n{fields_str}\n\nto {len(item_ids)} {entity_label}(s):\n{ids_str}\n"
    ).ask():
        return
    show_update_result_tabulated(update_fn(*item_ids, **update_kwargs))

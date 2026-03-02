import typer
import questionary
from typing import Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.enumerations import BaseEnum, ProductType
from capella_console_client.cli.visualize import show_cancel_result_tabulated, show_update_result_tabulated
from capella_console_client.cli.validate import _validate_uuid


app = typer.Typer(help="Manage Tasking requests")


def _validate_tr_ids(text: str) -> bool | str:
    """
    Validate comma-separated tasking request IDs (UUIDs).
    Returns True if valid, error message string if invalid.
    """
    if not text or not text.strip():
        return "At least one tasking request ID is required"

    tr_ids = [tr_id.strip() for tr_id in text.split(",")]

    for tr_id in tr_ids:
        result = _validate_uuid(tr_id)
        if result is not True:
            return f"Invalid UUID '{tr_id}': {result}"

    return True


@app.command(help="interactively manage tasking requests")
def interactive():
    interactive_manage_trs()


@app.command(help="cancel tasking requests")
def cancel():
    _cancel_trs()


@app.command(help="update tasking requests")
def update():
    _update_trs()


def _fetch_users() -> list[dict[str, Any]]:
    """
    Fetch users from the API and prompt the user to select one.
    Returns the selected user's UUID or None if cancelled.
    """
    users = []
    page_cnt = 1

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        # First request to get total pages
        resp = CLIENT._sesh.get(f"/users/?limit=1000&page={page_cnt}")
        page = resp.json()
        total_pages = page["totalPages"]

        task = progress.add_task(f"[cyan]Fetching users...", total=total_pages)

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
    """
    Fetch organizations from the API.
    Returns list of organization dictionaries.
    """
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

        task = progress.add_task(f"[cyan]Fetching organizations...", total=total_pages)

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
    """
    Prompt admin to select a target user or organization for tasking request operations.

    Prompts the admin to:
    1. Choose between user or org
    2. Choose selection method (manual UUID entry or fetch from API)
    3. If fetching from API, select from autocomplete list

    Returns:
        Tuple of (target_type, target_uuid) where:
        - target_type is "user" or "org"
        - target_uuid is the selected entity's UUID
        Returns (None, None) if user cancels at any prompt.
    """
    # First prompt: select user or org
    admin_for_who = questionary.select(
        "for who:",
        choices=["user", "org"],
    ).ask()

    if not admin_for_who:
        return (None, None)

    # Second prompt: selection method (customized based on first choice)
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

            # Create email -> user_id mapping
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

            # Create name -> org_id mapping
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


class TrManageOptions(str, BaseEnum):
    cancel = "cancel"
    update = "update"

    @classmethod
    def _get_choices(cls):
        return list(TrManageOptions)


class TrScopeOptions(str, BaseEnum):
    user = "current user"
    org = "current organization (requires elevated perms)"
    admin = "admin (requires elevated perms)"
    tasking_request_id = "by tasking request ID"

    @classmethod
    def _get_choices(cls):
        whoami = CLIENT.whoami()
        valid = [cls.user, cls.tasking_request_id]
        if "organization-manager" in whoami["roles"]:
            valid.append(cls.org)
        if "admin" in whoami["roles"]:
            valid.append(cls.admin)
        return valid


def _prompt_tr_selection(action: str, base_search_kwargs: dict | None = None) -> list[str] | None:
    """
    Prompt for scope, search for matching TRs, and let the user pick via checkbox.
    Returns the selected tasking request IDs, or None if the user aborted at any step.
    """
    for_who_choices = TrScopeOptions._get_choices()

    if len(for_who_choices) > 1:
        for_who = questionary.select(f"{action.capitalize()} tasking requests of ?", choices=for_who_choices).ask()
    else:
        for_who = TrScopeOptions.user

    tr_search_kwargs = {**(base_search_kwargs or {})}

    if for_who == TrScopeOptions.org:
        tr_search_kwargs["for_org"] = True
    elif for_who == TrScopeOptions.admin:
        admin_for_who, admin_uuid = _prompt_admin_target()
        if not admin_for_who:
            return None
        if admin_for_who == "user":
            tr_search_kwargs["user_id"] = admin_uuid
        elif admin_for_who == "org":
            tr_search_kwargs["org_id"] = [admin_uuid]
    elif for_who == TrScopeOptions.tasking_request_id:
        tr_ids_input = questionary.text(
            "Enter tasking request ID(s) (comma-separated for multiple):",
            validate=lambda text: _validate_tr_ids(text),
        ).ask()
        if not tr_ids_input:
            return None
        tr_search_kwargs["tasking_request_id"] = [tr_id.strip() for tr_id in tr_ids_input.split(",")]

    trs = CLIENT.search_tasking_requests(**tr_search_kwargs, show_progress=True)

    if not trs:
        typer.echo(f"No {action}able tasking requests found for {tr_search_kwargs=}...")
        return None

    id_by_tr_option = {_form_tr_overview(tr): tr["properties"]["taskingrequestId"] for tr in trs}
    selection = questionary.checkbox("Which tasking request?", choices=list(id_by_tr_option.keys())).ask()

    if not selection:
        typer.echo("Nothing selected ... aborting")
        return None

    return [id_by_tr_option[t] for t in selection]


def interactive_manage_trs():
    start_from_opt = questionary.select("What would you like to do?", choices=TrManageOptions._get_choices()).ask()

    if start_from_opt == TrManageOptions.cancel:
        _cancel_trs()
    elif start_from_opt == TrManageOptions.update:
        _update_trs()


def _cancel_trs():
    tr_ids = _prompt_tr_selection(
        action="cancel", base_search_kwargs={"status": ["received", "review", "submitted", "active", "accepted"]}
    )
    if tr_ids is None:
        return

    selection_str = "\n".join(f" - {tr_id}" for tr_id in tr_ids)
    if questionary.confirm(
        f"Please confirm you'd like to cancel the following tasking requests (cancelation charges might apply):\n\n{selection_str}\n"
    ).ask():
        cancel_result = CLIENT.cancel_tasking_requests(*tr_ids)
        show_cancel_result_tabulated(cancel_result)


_TRS_UPDATABLE_FIELD_LABELS: dict[str, str] = {
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
        choices=list(_TRS_UPDATABLE_FIELD_LABELS.values()),
    ).ask()

    if not selected_labels:
        return None

    label_to_kwarg = {v: k for k, v in _TRS_UPDATABLE_FIELD_LABELS.items()}
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


def _update_trs():
    tr_ids = _prompt_tr_selection(action="update")
    if tr_ids is None:
        return

    update_kwargs = _prompt_update_fields()
    if not update_kwargs:
        return

    fields_str = "\n".join(f"  {_TRS_UPDATABLE_FIELD_LABELS[k]}: {v!r}" for k, v in update_kwargs.items())
    tr_ids_str = "\n".join(f" - {tr_id}" for tr_id in tr_ids)
    if not questionary.confirm(
        f"Apply the following updates:\n{fields_str}\n\nto {len(tr_ids)} tasking request(s):\n{tr_ids_str}\n"
    ).ask():
        return

    result = CLIENT.update_tasking_requests(*tr_ids, **update_kwargs)
    show_update_result_tabulated(result)


def _form_tr_overview(tr):
    tr_props = tr["properties"]
    tr_name = tr_props["taskingrequestName"]
    tr_description = tr_props["taskingrequestDescription"]
    tr_id = tr_props["taskingrequestId"]

    overview = ""
    if tr_name:
        overview += f"{tr_name} · "

    if tr_description:
        overview += f"{tr_description} "

    overview += f"({tr_id})"
    return overview

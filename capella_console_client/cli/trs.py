import typer
import questionary
from typing import Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.visualize import show_cancel_result_tabulated
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
        resp = CLIENT._sesh.get(f"/organizations/?limit=1000&page={page_cnt}")
        page = resp.json()
        total_pages = page["totalPages"]

        task = progress.add_task(f"[cyan]Fetching organizations...", total=total_pages)

        orgs.extend(page["results"])
        progress.update(task, advance=1)

        if page["currentPage"] == page["totalPages"]:
            return orgs

        page_cnt += 1

        while page_cnt <= total_pages:
            resp = CLIENT._sesh.get(f"/organizations/?limit=1000&page={page_cnt}")
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

    @classmethod
    def _get_choices(cls):
        return list(TrManageOptions)


class TrCancelOptions(str, BaseEnum):
    user = "current user"
    org = "current organization (requires elevated perms)"
    admin = "admin (requires elevated perms)"
    tasking_request_id = "by tasking request ID"

    @classmethod
    def _get_choices(cls):
        # sub-select valid choices
        whoami = CLIENT.whoami()

        valid = [TrCancelOptions.user, TrCancelOptions.tasking_request_id]

        if "organization-manager" in whoami["roles"]:
            valid.append(TrCancelOptions.org)

        if "admin" in whoami["roles"]:
            valid.append(TrCancelOptions.admin)

        return valid


def interactive_manage_trs():
    start_from_opt = questionary.select("What would you like to do?", choices=TrManageOptions._get_choices()).ask()

    if start_from_opt == TrManageOptions.cancel:
        _cancel_trs()


def _cancel_trs():
    for_who_choices = TrCancelOptions._get_choices()
    should_prompt = len(for_who_choices) > 1

    if should_prompt:
        for_who = questionary.select("Cancel tasking requests of ?", choices=TrCancelOptions._get_choices()).ask()
    else:
        for_who = TrCancelOptions.user

    tr_search_kwargs = dict(status=["received", "review", "submitted", "active", "accepted"])
    if for_who == TrCancelOptions.org:
        tr_search_kwargs["for_org"] = True
    elif for_who == TrCancelOptions.admin:
        admin_for_who, admin_uuid = _prompt_admin_target()
        if not admin_for_who:
            return

        if admin_for_who == "user":
            tr_search_kwargs["user_id"] = admin_uuid
        elif admin_for_who == "org":
            tr_search_kwargs["org_id"] = [admin_uuid]
    elif for_who == TrCancelOptions.tasking_request_id:
        tr_ids_input = questionary.text(
            "Enter tasking request ID(s) (comma-separated for multiple):",
            validate=lambda text: _validate_tr_ids(text),
        ).ask()

        if not tr_ids_input:
            return

        # Parse comma-separated IDs
        tr_ids = [tr_id.strip() for tr_id in tr_ids_input.split(",")]
        tr_search_kwargs["tasking_request_id"] = tr_ids

    trs = CLIENT.search_tasking_requests(**tr_search_kwargs)

    if not trs:
        typer.echo(f"No cancelable tasking requests found for {tr_search_kwargs=}...")
        return

    id_by_tr_option = {_form_tr_overview(tr): tr["properties"]["taskingrequestId"] for tr in trs}
    selection = questionary.checkbox("Which tasking request?", choices=id_by_tr_option.keys()).ask()

    if not selection:
        typer.echo("Nothing selected ... aborting")
        return

    trs_ids_to_cancel = [id_by_tr_option[t] for t in selection]

    selection_str = [f" - {cur}" for cur in selection]
    if questionary.confirm(
        f"Please confirm you'd like to cancel the following tasking requests (cancelation charges might apply):\n\n{'\n'.join(selection_str)}\n"
    ).ask():
        cancel_result = CLIENT.cancel_tasking_requests(*trs_ids_to_cancel)
        show_cancel_result_tabulated(cancel_result)


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

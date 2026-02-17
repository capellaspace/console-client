import typer
import questionary


from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.enumerations import BaseEnum
from capella_console_client.cli.visualize import show_cancel_result_tabulated
from capella_console_client.cli.validate import _validate_uuid


app = typer.Typer(help="Manage Tasking requests")


class TrManageOptions(str, BaseEnum):
    cancel = "cancel"

    @classmethod
    def _get_choices(cls):
        return list(TrManageOptions)


class TrCancelOptions(str, BaseEnum):
    user = "current user"
    org = "current organization (requires elevated perms)"
    admin = "admin (requires elevated perms)"

    @classmethod
    def _get_choices(cls):
        # sub-select valid choices
        whoami = CLIENT.whoami()

        valid = [TrCancelOptions.user]

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

    tr_search_payload = dict(status=["received", "review", "submitted", "active", "accepted"])
    if for_who == TrCancelOptions.org:
        tr_search_payload["for_org"] = True
    elif for_who == TrCancelOptions.admin:
        admin_responses = questionary.prompt(
            [
                {
                    "type": "select",
                    "name": "for_who",
                    "message": "for who:",
                    "choices": ["user", "org"],
                },
                {
                    "type": "text",
                    "name": "uuid",
                    "message": "uuid:",
                    "validate": _validate_uuid,
                },
            ]
        )

        amdin_for_who = admin_responses.get("for_who")
        admin_uuid = admin_responses.get("uuid")

        if not admin_for_who or not admin_uuid:
            return

        if admin_for_who == "user":
            tr_search_payload["userId"] = admin_uuid

        if admin_for_who == "org":
            tr_search_payload["organizationIds"] = [admin_uuid]

    trs = CLIENT.search_tasking_requests(**tr_search_payload)

    if not trs:
        typer.echo(f"No cancelable tasking requests found for {tr_search_payload=}...")
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

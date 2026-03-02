import typer
from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.prompt_helpers import _cancel_items, _update_items

app = typer.Typer(help="Manage tasking requests")

_CANCEL_STATUSES = ["received", "review", "submitted", "active", "accepted"]


@app.command(help="cancel tasking requests")
def cancel():
    _cancel_items(
        search_fn=CLIENT.search_tasking_requests,
        cancel_fn=CLIENT.cancel_tasking_requests,
        overview_fn=_form_task_overview,
        entity_label="tasking request",
        cancel_statuses=_CANCEL_STATUSES,
        id_search_kwarg="tasking_request_id",
    )


@app.command(help="update tasking requests")
def update():
    _update_items(
        search_fn=CLIENT.search_tasking_requests,
        update_fn=CLIENT.update_tasking_requests,
        overview_fn=_form_task_overview,
        entity_label="tasking request",
        id_search_kwarg="tasking_request_id",
    )


def _form_task_overview(tr) -> str:
    props = tr["properties"]
    overview = ""
    if props["taskingrequestName"]:
        overview += f"{props['taskingrequestName']} · "
    if props["taskingrequestDescription"]:
        overview += f"{props['taskingrequestDescription']} "
    overview += f"({props['taskingrequestId']})"
    return overview

import typer

from capella_console_client.cli.client_singleton import CLIENT
from capella_console_client.cli.prompt_helpers import _cancel_items, _update_items

app = typer.Typer(help="Manage repeat requests")

_CANCEL_STATUSES = ["received", "review", "submitted", "active", "accepted"]


@app.command(help="cancel repeat requests")
def cancel():
    _cancel_items(
        search_fn=CLIENT.search_repeat_requests,
        cancel_fn=CLIENT.cancel_repeat_requests,
        overview_fn=_form_repeat_overview,
        entity_label="repeat request",
        cancel_statuses=_CANCEL_STATUSES,
        id_search_kwarg="repeat_request_id",
    )


@app.command(help="update repeat requests")
def update():
    _update_items(
        search_fn=CLIENT.search_repeat_requests,
        update_fn=CLIENT.update_repeat_requests,
        overview_fn=_form_repeat_overview,
        entity_label="repeat request",
        id_search_kwarg="repeat_request_id",
    )


def _form_repeat_overview(rr) -> str:
    props = rr["properties"]
    overview = ""
    if props["repeatrequestName"]:
        overview += f"{props['repeatrequestName']} · "
    if props["repeatrequestDescription"]:
        overview += f"{props['repeatrequestDescription']} "
    overview += f"({props['repeatrequestId']})"
    return overview

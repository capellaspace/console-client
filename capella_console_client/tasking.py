from typing import Optional, Dict, Any, List

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import _validate_uuid
from capella_console_client.config import TASKING_REQUEST_DEFAULT_PAGE_SIZE
from capella_console_client.logconf import logger


def get_tasking_requests(
    *tasking_request_ids: Optional[str],
    session: CapellaConsoleSession,
    for_org: Optional[bool] = False,
    status: Optional[str] = None,
):
    if tasking_request_ids:
        return _get_tasking_requests_from_ids(*tasking_request_ids, session=session, status=status)

    tasking_requests = []
    page_cnt = 1
    params = {"page": page_cnt, "limit": TASKING_REQUEST_DEFAULT_PAGE_SIZE}
    if for_org:
        params["organizationId"] = session.organization_id
    else:
        params["customerId"] = session.customer_id

    logger.info(f"getting tasking requests for {params}")

    while True:
        if page_cnt != 1:
            logger.info(f"\tpage {page_cnt} out of {con['totalPages']}")

        resp = session.get("/tasks/paged", params=params)
        con: Dict[str, Any] = resp.json()
        tasking_requests.extend(con["results"])
        if con["currentPage"] >= con["totalPages"]:
            break
        page_cnt += 1
        params["page"] = page_cnt

    if status:
        tasking_requests = _filter_by_status(tasking_requests, status)

    if not tasking_requests:
        logger.info("found no tasking requests matching")
    else:
        multiple_suffix = "s" if len(tasking_requests) > 1 else ""
        logger.info(f"found {len(tasking_requests)} tasking request{multiple_suffix}")
    return tasking_requests


def _filter_by_status(tasking_requests: List[Dict[str, Any]], status: str):
    return [tr for tr in tasking_requests if _task_contains_status(tr, status)]


def _task_contains_status(task: Dict[str, Any], status_name: str) -> bool:
    return status_name.lower() in (s["code"] for s in task["properties"]["statusHistory"])


def _get_tasking_requests_from_ids(
    *tasking_request_ids: Optional[str], session: CapellaConsoleSession, status: Optional[str] = None
):
    for t_req_id in tasking_request_ids:
        _validate_uuid(t_req_id)

    # TODO: performant search
    tasking_requests = [session.get(f"/task/{tr_id}").json() for tr_id in tasking_request_ids]  # type: ignore
    if status:
        tasking_requests = _filter_by_status(tasking_requests, status)
    return tasking_requests

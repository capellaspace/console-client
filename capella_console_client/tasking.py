from typing import Optional, Dict, Any, List
from datetime import datetime

import dateutil.parser

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import _validate_uuid
from capella_console_client.config import TASKING_REQUEST_DEFAULT_PAGE_SIZE
from capella_console_client.logconf import logger
from capella_console_client.enumerations import TaskingRequestStatus


def get_tasking_requests(
    *tasking_request_ids: Optional[str],
    session: CapellaConsoleSession,
    for_org: Optional[bool] = False,
    **kwargs: Optional[Dict[str, Any]],
):
    # TODO: pydantic validation of kwargs

    if tasking_request_ids:
        return _get_tasking_requests_from_ids(*tasking_request_ids, session=session, **kwargs)

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

        # results are sorted by submissionTime - stop early if page is already over
        if kwargs.get("submission_time__gt") and not _is_greater_than_submission_time(
            tasking_requests[-1], kwargs["submission_time__gt"]  # type: ignore
        ):
            break

    tasking_requests = _filter(tasking_requests, **kwargs)

    if not tasking_requests:
        logger.info("found no tasking requests matching")
    else:
        multiple_suffix = "s" if len(tasking_requests) > 1 else ""
        logger.info(f"found {len(tasking_requests)} tasking request{multiple_suffix}")
    return tasking_requests


def _get_tasking_requests_from_ids(
    *tasking_request_ids: Optional[str], session: CapellaConsoleSession, **kwargs: Optional[Dict[str, Any]]
):
    for t_req_id in tasking_request_ids:
        _validate_uuid(t_req_id)

    # TODO: performant search
    tasking_requests = [session.get(f"/task/{tr_id}").json() for tr_id in tasking_request_ids]  # type: ignore

    tasking_requests = _filter(tasking_requests, **kwargs)
    return tasking_requests


def _filter_by_status(tasking_requests: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
    if status.lower() not in TaskingRequestStatus:
        logger.warning(f"{status} is not a valid TaskingRequestStatus ... omitting")
        return tasking_requests

    return [tr for tr in tasking_requests if _task_contains_status(tr, status)]


def _task_contains_status(task: Dict[str, Any], status_name: str) -> bool:
    return status_name.lower() in (s["code"] for s in task["properties"]["statusHistory"])


def _filter_by_submission_time(tasking_requests: List[Dict[str, Any]], submission_time__gt: datetime):
    return [cur for cur in tasking_requests if _is_greater_than_submission_time(cur, submission_time__gt)]


def _is_greater_than_submission_time(tasking_request: Dict[str, Any], submission_time__gt: datetime) -> bool:
    return dateutil.parser.parse(tasking_request["properties"]["submissionTime"], ignoretz=True) > submission_time__gt


REGISTERED_FILTERS = {"status": _filter_by_status, "submission_time__gt": _filter_by_submission_time}


def _filter(tasking_requests: List[Dict[str, Any]], **kwargs: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for filter_name, filter_value in kwargs.items():
        fct = REGISTERED_FILTERS.get(filter_name)
        if fct is None:
            logger.warning(f"filter {filter_name} unknown ... omitting")
            continue

        tasking_requests = fct(tasking_requests, filter_value)  # type: ignore

    return tasking_requests

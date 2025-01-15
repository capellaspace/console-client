from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, timedelta

import geojson
from dateutil.parser import parse

from capella_console_client.logconf import logger
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import (
    _validate_uuid,
    _snake_to_camel,
    _datetime_to_iso8601_str,
    _set_squint_default,
)
from capella_console_client.config import TASKING_REQUEST_DEFAULT_PAGE_SIZE, TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS
from capella_console_client.enumerations import (
    TaskingRequestStatus,
    ObservationDirection,
    OrbitState,
    ProductType,
    OrbitalPlane,
    CollectionTier,
    Polarization,
    ArchiveHoldback,
    LocalTimeOption,
    SquintMode,
    CollectionType,
)


def create_tasking_request(
    session: CapellaConsoleSession,
    geometry: geojson.geometry.Geometry,
    name: str,
    description: Optional[str] = "",
    collection_type: Optional[Union[CollectionType, str]] = CollectionType.SPOTLIGHT,
    collection_tier: Optional[Union[CollectionTier, str]] = CollectionTier.standard,
    window_open: Optional[Union[datetime, str]] = None,
    window_close: Optional[Union[datetime, str]] = None,
    local_time: Optional[Union[LocalTimeOption, List[int]]] = None,
    product_types: Optional[List[Union[ProductType, str]]] = None,
    off_nadir_min: Optional[int] = None,
    off_nadir_max: Optional[int] = None,
    image_width: Optional[int] = None,
    orbital_planes: Optional[List[Union[OrbitalPlane, int]]] = None,
    asc_dsc: Optional[Union[OrbitState, str]] = OrbitState.either,
    look_direction: Optional[Union[ObservationDirection, str]] = ObservationDirection.either,
    polarization: Optional[Union[Polarization, str]] = None,
    archive_holdback: Optional[Union[ArchiveHoldback, str]] = ArchiveHoldback.none,
    custom_attribute_1: Optional[str] = None,
    custom_attribute_2: Optional[str] = None,
    pre_approval: bool = False,
    azimuth_angle_min: Optional[int] = None,
    azimuth_angle_max: Optional[int] = None,
    squint: Optional[Union[SquintMode, str]] = None,
    max_squint_angle: Optional[int] = None,
) -> Dict[str, Any]:

    window_open, window_close = _set_window_open_close(window_open, window_close)

    if squint is None:
        squint = _set_squint_default(geometry)

    loc = locals()
    collect_constraints = {
        _snake_to_camel(k): loc[k]
        for k in TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS
        if k in loc and loc[k] is not None
    }

    payload = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "taskingrequestName": name,
            "taskingrequestDescription": description,
            "windowOpen": window_open,
            "windowClose": window_close,
            "collectionTier": collection_tier,
            "collectionType": collection_type,
            "archiveHoldback": archive_holdback,
            "customAttribute1": custom_attribute_1,
            "customAttribute2": custom_attribute_2,
            "pre_approval": pre_approval,
            "collectConstraints": collect_constraints,
        },
    }

    if product_types is not None:
        payload["properties"]["processingConfig"] = {"productTypes": product_types}

    return session.post("/task", json=payload).json()


def _set_window_open_close(
    window_open: Optional[Union[datetime, str]], window_close: Optional[Union[datetime, str]]
) -> Tuple[str, str]:
    if window_open is None:
        window_open = datetime.utcnow()

    if window_close is None:
        if isinstance(window_open, str):
            window_open = parse(window_open)
        window_close = window_open + timedelta(days=7)

    window_open = _datetime_to_iso8601_str(window_open)
    window_close = _datetime_to_iso8601_str(window_close)
    return (window_open, window_close)


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
    return parse(tasking_request["properties"]["submissionTime"], ignoretz=True) > submission_time__gt


REGISTERED_FILTERS = {"status": _filter_by_status, "submission_time__gt": _filter_by_submission_time}


def _filter(tasking_requests: List[Dict[str, Any]], **kwargs: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for filter_name, filter_value in kwargs.items():
        fct = REGISTERED_FILTERS.get(filter_name)
        if fct is None:
            logger.warning(f"filter {filter_name} unknown ... omitting")
            continue

        tasking_requests = fct(tasking_requests, filter_value)  # type: ignore

    return tasking_requests

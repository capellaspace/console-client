from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import geojson
from dateutil.parser import parse

from capella_console_client.logconf import logger
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import (
    _snake_to_camel,
    _datetime_to_iso8601_str,
    _set_squint_default,
)
from capella_console_client.config import (
    TASKING_REQUEST_DEFAULT_PAGE_SIZE,
    TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS,
    MAX_CONCURRENT_TASK_SEARCH,
    MAX_CONCURRENT_CANCEL,
    MIN_TASK_SEARCH_PAGE_SIZE,
)
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
from capella_console_client.exceptions import CapellaConsoleClientError
from capella_console_client.report import print_task_search_result


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
    contract_id: Optional[str] = None,
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

    if contract_id:
        payload["contractId"] = contract_id

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


def get_tasking_request(tasking_request_id: str, session: CapellaConsoleSession):
    task_response = session.get(f"/task/{tasking_request_id}")
    return task_response.json()


# TODO: extend StacSearch and return list[SearchResult]
def search_tasking_requests(
    *tasking_request_ids: Optional[str],
    session: CapellaConsoleSession,
    for_org: Optional[bool] = False,
    **kwargs: Optional[Dict[str, Any]],
):
    search_payload = _build_search_payload(*tasking_request_ids, session=session, for_org=for_org, **kwargs)

    # TODO: allow override of page_size / adhere to limit
    page_size = MIN_TASK_SEARCH_PAGE_SIZE

    logger.info(f"searching tasking requests with payload {search_payload}")
    first_page = _fetch_trs(session, params={"page": 1, "limit": page_size}, search_payload=search_payload)

    total_pages = first_page["totalPages"]
    fetch_more = total_pages > 1
    if not fetch_more:
        trs = first_page["results"]
        print_task_search_result(trs)
        return trs

    page_params = [{"page": i, "limit": page_size} for i in range(2, total_pages + 1)]

    _fetch_worker = partial(_fetch_trs, search_payload=search_payload, session=session)

    futures = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASK_SEARCH) as executor:
        for page_param in page_params:
            futures.append(executor.submit(_fetch_worker, params=page_param))

    trs = []
    for f in futures:
        page = f.result()
        trs.extend(page["results"])

    print_task_search_result(trs)
    return trs


def _build_search_payload(*tasking_request_id, session: CapellaConsoleSession, for_org: Optional[bool], **kwargs):
    # TODO: supported filters
    query = {"includeRepeatingTasks": False}

    if not session.organization_id or not session.customer_id:
        session._cache_user_info()

    if for_org:
        query["organizationIds"] = [session.organization_id]
    else:
        query["userId"] = session.customer_id

    _add_tasking_request_id_filter(*tasking_request_id, query=query)
    _add_status_filter(query, **kwargs)

    return {
        "query": query,
    }


def _add_tasking_request_id_filter(*tasking_request_id, query):
    if not tasking_request_id:
        return

    query["taskingrequestIds"] = list(tasking_request_id)


def _add_status_filter(query, **kwargs):
    if "status" not in kwargs:
        return

    status_arg = kwargs["status"]
    if isinstance(status_arg, str):
        status_arg = [status_arg]

    valid_status = [s.lower() for s in status_arg if s.lower() in TaskingRequestStatus]

    if not valid_status:
        logger.warning(f"No valid tasking request status provided ({kwargs['status']}) ... dropping from filter")

    query["lastStatusCode"] = valid_status


def _fetch_trs(session, search_payload, params):
    resp = session.post("/tasks/search", params=params, json=search_payload)
    page: Dict[str, Any] = resp.json()
    if page["currentPage"] > 1:
        logger.info(f"page {page['currentPage']} out of {page['totalPages']}: {len(page['results'])} tasking requests")
    return page


def _task_contains_status(task: Dict[str, Any], status_name: str) -> bool:
    return status_name.lower() in (s["code"] for s in task["properties"]["statusHistory"])


def cancel_tasking_requests(
    *tasking_request_ids: str,
    session: CapellaConsoleSession,
) -> Dict[str, Any]:
    return _cancel_multi_parallel(*tasking_request_ids, session=session, cancel_fct=_cancel_tasking_request)


def _cancel_multi_parallel(*cancel_ids: str, session, cancel_fct):
    max_workers = min(MAX_CONCURRENT_CANCEL, len(cancel_ids))

    results_by_cancel_id = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures_by_cancel_id = {}

        for _id in cancel_ids:
            futures_by_cancel_id[_id] = executor.submit(
                cancel_fct,
                session=session,
                cancel_id=_id,
            )

        for key, fut in futures_by_cancel_id.items():
            results_by_cancel_id[key] = fut.result()

    return results_by_cancel_id


def _cancel_tasking_request(session: CapellaConsoleSession, cancel_id: str):
    return _cancel_worker(session=session, endpoint=f"task/{cancel_id}/status")


def _cancel_worker(session: CapellaConsoleSession, endpoint: str):
    try:
        session.patch(endpoint, json={"status": "canceled"})
    except CapellaConsoleClientError as exc:
        if exc.response is not None:
            return {"success": False, **exc.response.json()}
        return {"success": False}

    return {
        "success": True,
    }

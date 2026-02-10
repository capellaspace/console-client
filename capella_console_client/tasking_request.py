from typing import Optional, Dict, Any, List, Union, Tuple, DefaultDict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from copy import deepcopy
from collections import defaultdict

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
    TR_SEARCH_DEFAULT_PAGE_SIZE,
    TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS,
    TR_MAX_CONCURRENCY,
    TR_CANCEL_MAX_CONCURRENCY,
    SUPPORTED_TASKING_REQUEST_SEARCH_QUERY_FIELDS,
    OPERATOR_SUFFIXES,
    TR_FILTERS_BY_QUERY_FIELDS,
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
from capella_console_client.search import AbstractSearch, SearchResult


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


class TaskingRequestSearchResult(SearchResult):
    def add(self, page: Dict[str, Any], keep_duplicates: bool = False) -> int:
        self._pages.append(page)
        self._features.extend(page["results"])
        return len(page["results"])


class TaskingRequestSearch(AbstractSearch):
    def __init__(self, session: CapellaConsoleSession, **kwargs) -> None:
        self.session = session
        self.payload: Dict[str, Any] = {}
        self.threaded = kwargs.pop("threaded", False)
        self.page_size = kwargs.pop("page_size", None) or TR_SEARCH_DEFAULT_PAGE_SIZE

        # TODO: max results (limit)

        query_payload = self._get_query_payload(kwargs)
        if query_payload:
            self.payload["query"] = dict(query_payload)

        # sortby = cur_kwargs.pop("sortby", None)
        # if sortby:
        #     self.payload["sortby"] = self._get_sort_payload(sortby)

        # TODO: limit
        # if "limit" not in self.payload:
        #     self.payload["limit"] = CATALOG_DEFAULT_LIMIT

    def _get_sort_payload(self, sortby):
        raise RuntimeError("Not implemented")

    def _get_query_payload(self, kwargs) -> DefaultDict[str, Dict[str, Any]]:
        query_payload: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)
        query_payload["includeRepeatingTasks"] = {"eq": False}
        query_payload = self._add_user_org_query(query_payload, **kwargs)

        sntzr = TaskingRequestQuerySanitizer()

        for cur_field, value in kwargs.items():
            cur_field, op = self._split_op(cur_field)
            if cur_field not in SUPPORTED_TASKING_REQUEST_SEARCH_QUERY_FIELDS:
                logger.warning(f"filter {cur_field} not supported ... omitting")
                continue

            if op not in OPERATOR_SUFFIXES:
                logger.warning(f"operator {op} not supported ... omitting")
                continue

            target_field = TR_FILTERS_BY_QUERY_FIELDS.get(cur_field, cur_field)

            if sntzr.has_sanitizer(cur_field):
                value = sntzr.sanitize(field=cur_field, value=value)

            # op == in currently not supported by api
            # TODO: replace direct assignment (no operator) once in supported
            if isinstance(value, list):
                query_payload[target_field] = value  # type: ignore[assignment]
                continue

            query_payload[target_field][op] = value

        return query_payload

    def _add_user_org_query(self, query_payload, **kwargs):
        # TODO: resellerId?
        any_of = ("org_id", "user_id")

        if any(x in kwargs for x in any_of):
            return query_payload

        if not self.session.customer_id:
            self.session._cache_user_info()

        # TODO: should the endpoint fill this in?
        query_payload["userId"] = self.session.customer_id
        return query_payload

    def fetch_all(self) -> TaskingRequestSearchResult:
        search_result = TaskingRequestSearchResult(entity="tasking request", request_body=self.payload)
        logger.info(f"searching tasking requests with payload {self.payload}")
        first_page = _fetch_trs(self.session, params={"page": 1, "limit": self.page_size}, search_payload=self.payload)

        total_pages = first_page["totalPages"]
        fetch_more = total_pages > 1

        if not fetch_more:
            search_result.add(first_page)
            print_task_search_result(search_result._features)
            return search_result

        page_params = [{"page": i, "limit": self.page_size} for i in range(2, total_pages + 1)]

        _fetch_worker = partial(_fetch_trs, search_payload=self.payload, session=self.session)

        with ThreadPoolExecutor(max_workers=TR_MAX_CONCURRENCY) as executor:
            results = executor.map(_fetch_worker, page_params)

        for page in results:
            search_result.add(page)

        print_task_search_result(search_result._features)
        return search_result


class TaskingRequestQuerySanitizer:

    SUPPORTED = {"status"}

    @classmethod
    def has_sanitizer(cls, field) -> bool:
        return field in TaskingRequestQuerySanitizer.SUPPORTED

    def sanitize(cls, field, value):
        if not cls.has_sanitizer(field):
            # TODO: logger
            return value

        return {"status": cls._sanitize_status_filter}[field](value)

    def _sanitize_status_filter(cls, value):
        is_string = isinstance(value, str)
        if is_string:
            value = [value]

        valid_status = [s.lower() for s in value if s.lower() in TaskingRequestStatus]

        if not valid_status:
            logger.warning(f"No valid tasking request status provided ({value}) ... dropping from filter")
            return None

        if is_string:
            return valid_status[0]

        return valid_status


def _fetch_trs(session, search_payload, params):
    resp = session.post("/tasks/search", params=params, json=search_payload)
    page = resp.json()
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
    max_workers = min(TR_CANCEL_MAX_CONCURRENCY, len(cancel_ids))

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

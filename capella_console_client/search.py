from typing import Any, Dict, Tuple, List, DefaultDict, Optional
from collections import defaultdict

import httpx
from retrying import retry  # type: ignore

from capella_console_client.logconf import logger
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.config import (
    ALL_SUPPORTED_FIELDS,
    ALL_SUPPORTED_SORTBY,
    SUPPORTED_SEARCH_FIELDS,
    SUPPORTED_QUERY_FIELDS,
    STAC_PREFIXED_BY_QUERY_FIELDS,
    OPERATOR_SUFFIXES,
    DEFAULT_PAGE_SIZE,
    DEFAULT_MAX_FEATURE_COUNT,
    API_GATEWAY,
)
from capella_console_client.hooks import retry_if_http_status_error


def _build_search_payload(**kwargs) -> Dict[str, Any]:
    payload = {}
    query_payload: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)

    for field, value in kwargs.items():
        field, op = _split_op(field)
        if field not in ALL_SUPPORTED_FIELDS:
            logger.warning(f"filter {field} not supported ... omitting")
            continue

        if op not in OPERATOR_SUFFIXES:
            logger.warning(f"operator {op} not supported ... omitting")
            continue

        if field in SUPPORTED_SEARCH_FIELDS:
            payload[field] = value
        elif field in SUPPORTED_QUERY_FIELDS:
            if type(value) == list:
                op = "in"

            target_field = STAC_PREFIXED_BY_QUERY_FIELDS.get(field, field)
            query_payload[target_field][op] = value

    if query_payload:
        payload["query"] = dict(query_payload)

    if "sortby" in kwargs:
        payload["sortby"] = _get_sort_payload(kwargs)

    return payload


def _get_sort_payload(kwargs):
    directions = {"-": "desc", "+": "asc"}
    sorts = []
    orig = kwargs["sortby"]

    if not isinstance(orig, list):
        orig = [orig]

    for sort_arg in orig:
        field = sort_arg[1:]
        direction = sort_arg[0]
        if direction not in directions:
            direction = "+"
            field = sort_arg

        if field not in ALL_SUPPORTED_SORTBY:
            logger.warning(f"sorting by {field} not supported ... omitting")
            continue

        if field in SUPPORTED_QUERY_FIELDS or field == "datetime":
            field = f"properties.{field}"

        sorts.append({"field": field, "direction": directions[direction]})
    return sorts


def _split_op(field: str) -> Tuple[str, str]:
    parts = field.split("__")
    if len(parts) == 2:
        op = parts[1]
    else:
        op = "eq"
    return (parts[0], op)


def _paginated_search(
    session: CapellaConsoleSession, payload: Dict[str, Any]
) -> List[Dict[str, Any]]:
    requested_limit = payload.get("limit", DEFAULT_MAX_FEATURE_COUNT)

    if "limit" not in payload:
        payload["limit"] = DEFAULT_MAX_FEATURE_COUNT

    # ensure DEFAULT_PAGE_SIZE if requested limit > DEFAULT_PAGE_SIZE
    payload["limit"] = min(DEFAULT_PAGE_SIZE, payload["limit"])

    page_cnt = 1
    features: List[Dict[str, Any]] = []
    next_href = None

    with session:
        while True:
            _log_page_query(page_cnt, len(features), payload["limit"])
            page_data = _page_search(session, payload, next_href)
            features.extend(page_data["features"])

            limit_reached = len(features) >= requested_limit
            if limit_reached:
                break

            next_href = _get_next_page_href(page_data)
            if next_href is None:
                break

            payload["limit"] = min(requested_limit - len(features), DEFAULT_PAGE_SIZE)
            page_cnt += 1
            payload["page"] = page_cnt

    len_feat = len(features)

    # truncate to limit
    if len_feat > requested_limit:
        features = features[:requested_limit]

    if not len_feat:
        logger.info(f"found no STAC items matching your query")
    else:
        multiple_suffix = "s" if len_feat > 1 else ""
        logger.info(f"found {len(features)} STAC item{multiple_suffix}")

    return features


def _get_next_page_href(page_data: Dict[str, Any]) -> Optional[str]:
    links = page_data.get("links", [])
    try:
        next_href = next(filter(lambda c: c["rel"] == "next", links))["href"]
    except StopIteration:
        next_href = None

    return next_href


def _log_page_query(page_cnt: int, len_feat: int, limit: int):
    logger.info(f"\tpage {page_cnt} ({len_feat} - {len_feat + limit})")


@retry(
    retry_on_exception=retry_if_http_status_error,
    wait_exponential_multiplier=1000,
    stop_max_delay=16000,
)
def _page_search(
    session: CapellaConsoleSession, payload: Dict[str, Any], next_href: str = None
) -> Dict[str, Any]:
    endpoint = f"{API_GATEWAY}/search" if next_href is None else next_href

    # TODO: better mechanism
    # fallback in case API gateway endpoint changed, i.e. re-deployment
    try:
        resp = session.post(endpoint, json=payload)
    except httpx.ConnectError as e:
        logger.warning(f"{endpoint}: {e} - retrying with /catalog/search")
        resp = session.post("/catalog/search", json=payload)

    data = resp.json()
    return data

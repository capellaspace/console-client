from typing import Any, Dict, Tuple, List, DefaultDict
from collections import defaultdict


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
    max_cnt = payload.get("limit", DEFAULT_MAX_FEATURE_COUNT)

    # ensure DEFAULT_PAGE_SIZE independently if custom limit > 500
    if "limit" not in payload or payload["limit"] > DEFAULT_PAGE_SIZE:
        payload["limit"] = DEFAULT_PAGE_SIZE

    page = 1
    features = []
    next_href = None
    with session:
        while True:
            con = _page_search(session, payload, next_href)
            features.extend(con["features"])
            limit_reached = len(features) >= max_cnt
            links = con.get("links", [])

            try:
                next_href = next(filter(lambda c: c["rel"] == "next", links))["href"]
                has_next_page = True
            except StopIteration:
                has_next_page = False
            if not has_next_page or limit_reached:
                break

            page += 1
            logger.info(
                f"\tpage {page} ({(page-1) * payload['limit']} - {page * payload['limit']})"
            )
            payload["page"] = page

    len_feat = len(features)

    if not len_feat:
        logger.info(f"found no STAC items matching your query")
    else:
        multiple_suffix = "s" if len_feat > 1 else ""
        logger.info(f"found {len(features)} STAC item{multiple_suffix}")
    return features


@retry(
    retry_on_exception=retry_if_http_status_error,
    wait_exponential_multiplier=1000,
    stop_max_delay=16000,
)
def _page_search(
    session: CapellaConsoleSession, payload: Dict[str, Any], next_href: str
) -> Dict[str, Any]:
    if next_href is None:
        resp = session.post("/catalog/search", json=payload)
    else:
        resp = session.post(next_href, json=payload)
    body = resp.json()
    return body

from copy import deepcopy
from typing import Any, Dict, Tuple, DefaultDict, Optional, List
from collections import defaultdict
from urllib.parse import urlparse
from dataclasses import dataclass, field

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
    CATALOG_DEFAULT_PAGE_SIZE,
    CATALOG_DEFAULT_MAX_FEATURE_COUNT,
)
from capella_console_client.hooks import retry_if_http_status_error, log_attempt_delay


@dataclass
class SearchResult:

    request_body: Dict[str, Any] = field(default_factory=dict)
    _pages: List[Dict[str, Any]] = field(default_factory=list)
    _features: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, page: Dict[str, Any], keep_duplicates: bool = False) -> int:
        if not keep_duplicates:
            page = self._filter_dupes(page)
        self._pages.append(page)
        self._features.extend(page["features"])
        return len(page["features"])

    def _filter_dupes(self, page: Dict[str, Any]) -> Dict[str, Any]:
        # drop duplicates within page features
        page_stac_ids = [feat["id"] for feat in page["features"]]
        set_page_stac_ids = set(page_stac_ids)

        if len(set_page_stac_ids) != len(page["features"]):
            page["features"] = [page["features"][page_stac_ids.index(p_id)] for p_id in set_page_stac_ids]

        # drop duplicates within SearchResult
        dupes = set_page_stac_ids.intersection(self.stac_ids)

        if dupes:
            page["features"] = [p for p in page["features"] if p["id"] not in dupes]

        return page

    # backwards compability
    def __getitem__(self, key):
        return self._features.__getitem__(key)

    def __iter__(self):
        return self._features.__iter__()

    def __len__(self):
        return len(self._features)

    def __repr__(self):
        return f"{self.__class__} ({len(self)} STAC items)"

    def to_feature_collection(self):
        return {"type": "FeatureCollection", "features": self._features}

    @property
    def stac_ids(self):
        return [item["id"] for item in self._features]

    def merge(self, other: "SearchResult", keep_duplicates: bool = False) -> "SearchResult":
        copy = deepcopy(self)
        for page in other._pages:
            copy.add(page=page, keep_duplicates=keep_duplicates)

        return copy


class StacSearch:
    def __init__(self, session: CapellaConsoleSession, **kwargs) -> None:
        cur_kwargs = deepcopy(kwargs)
        self.session = session
        self.payload: Dict[str, Any] = {}

        sortby = cur_kwargs.pop("sortby", None)
        query_payload = self._get_query_payload(cur_kwargs)
        if query_payload:
            self.payload["query"] = dict(query_payload)

        if sortby:
            self.payload["sortby"] = self._get_sort_payload(sortby)

    def _get_query_payload(self, kwargs) -> DefaultDict[str, Dict[str, Any]]:
        query_payload: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)

        for cur_field, value in kwargs.items():
            cur_field, op = self._split_op(cur_field)
            if cur_field not in ALL_SUPPORTED_FIELDS:
                logger.warning(f"filter {cur_field} not supported ... omitting")
                continue

            if op not in OPERATOR_SUFFIXES:
                logger.warning(f"operator {op} not supported ... omitting")
                continue

            if cur_field in SUPPORTED_SEARCH_FIELDS:
                self.payload[cur_field] = value
            elif cur_field in SUPPORTED_QUERY_FIELDS:
                if type(value) == list:
                    op = "in"

                target_field = STAC_PREFIXED_BY_QUERY_FIELDS.get(cur_field, cur_field)
                query_payload[target_field][op] = value

        return query_payload

    def _split_op(self, cur_field: str) -> Tuple[str, str]:
        parts = cur_field.split("__")
        if len(parts) == 2:
            op = parts[1]
        else:
            op = "eq"
        return (parts[0], op)

    def _get_sort_payload(self, sortby):
        directions = {"-": "desc", "+": "asc"}
        sorts = []
        orig = sortby

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

    def fetch_all(self) -> SearchResult:
        logger.info(f"searching catalog with payload {self.payload}")

        requested_limit = self.payload.get("limit", CATALOG_DEFAULT_MAX_FEATURE_COUNT)

        if "limit" not in self.payload:
            self.payload["limit"] = CATALOG_DEFAULT_MAX_FEATURE_COUNT

        # ensure CATALOG_DEFAULT_PAGE_SIZE if requested limit > CATALOG_DEFAULT_PAGE_SIZE
        self.payload["limit"] = min(CATALOG_DEFAULT_PAGE_SIZE, self.payload["limit"])

        page_cnt = 1
        search_result = SearchResult(request_body=self.payload)
        next_href = None

        while True:
            _log_page_query(page_cnt, len(search_result), self.payload["limit"])
            page_data = _page_search(self.session, self.payload, next_href)
            number_matched = page_data["numberMatched"]
            items_added = search_result.add(page_data)

            limit_reached = len(search_result) >= requested_limit or len(search_result) >= number_matched

            # all dupes
            size_unchanged = items_added == 0
            if limit_reached or size_unchanged:
                break

            next_href = _get_next_page_href(page_data)
            if next_href is None:
                break

            if page_cnt == 1:
                logger.info(f"Matched a total of {number_matched} stac items")

            self.payload["limit"] = CATALOG_DEFAULT_PAGE_SIZE
            page_cnt += 1
            self.payload["page"] = page_cnt

        # truncate to limit
        len_features = len(search_result)
        if len_features > requested_limit:
            search_result._features = search_result._features[:requested_limit]

        if not len_features:
            logger.info("found no STAC items matching your query")
        else:
            multiple_suffix = "s" if len_features > 1 else ""
            logger.info(f"found {len(search_result)} STAC item{multiple_suffix}")

        return search_result


def _log_page_query(page_cnt: int, len_feat: int, limit: int):
    if page_cnt != 1:
        logger.info(f"\tpage {page_cnt} ({len_feat} - {len_feat + limit})")


def _get_next_page_href(page_data: Dict[str, Any]) -> Optional[str]:
    links = page_data.get("links", [])
    try:
        next_href: Optional[str] = next(filter(lambda c: c["rel"] == "next", links))["href"]
    except StopIteration:
        next_href = None

    return next_href


@retry(
    retry_on_exception=retry_if_http_status_error,
    wait_func=log_attempt_delay,
    wait_exponential_multiplier=1000,
    stop_max_delay=16000,
)
def _page_search(session: CapellaConsoleSession, payload: Dict[str, Any], next_href: str = None) -> Dict[str, Any]:
    if next_href:
        # STAC API to return normalized asset hrefs, not api gateway - fixing this here ...
        url_parsed = urlparse(next_href)
        if url_parsed.netloc != urlparse(session.search_url).netloc:
            next_href = f"{session.search_url}?{url_parsed.query}"

    url = session.search_url if next_href is None else next_href
    resp = session.post(url, json=payload)

    data: Dict[str, Any] = resp.json()
    return data

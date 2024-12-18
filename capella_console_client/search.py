from copy import deepcopy
from typing import Any, Dict, Tuple, DefaultDict, Optional, List
from collections import defaultdict
from urllib.parse import urlparse
from dataclasses import dataclass, field
from math import ceil
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat

from capella_console_client.logconf import logger
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.config import (
    ALL_SUPPORTED_FIELDS,
    ALL_SUPPORTED_SORTBY,
    SUPPORTED_SEARCH_FIELDS,
    SUPPORTED_QUERY_FIELDS,
    STAC_PREFIXED_BY_QUERY_FIELDS,
    OPERATOR_SUFFIXES,
    CATALOG_MAX_PAGE_SIZE,
    CATALOG_DEFAULT_LIMIT,
    STAC_MAX_ITEM_RETURN,
    ALL_SUPPORTED_GROUPBY_FIELDS,
    ROOT_LEVEL_GROUPBY_FIELDS,
    UNKNOWN_GROUPBY_FIELD,
)
from capella_console_client.enumerations import OwnershipOption


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

    def _truncate(self):
        len_features = len(self)
        requested_limit = self.request_body.get("limit")
        if requested_limit and len_features > requested_limit:
            self._features = self._features[:requested_limit]

    def _report(self):
        len_results = len(self)
        if not len_results:
            message = "found no STAC items matching your query"
        else:
            multiple_suffix = "s" if len_results > 1 else ""
            message = f"found {len_results} STAC item{multiple_suffix}"
        logger.info(message)

    # backwards compatibility
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

    @property
    def collect_ids(self):
        return [item["properties"].get("capella:collect_id", "N/A") for item in self._features]

    def merge(self, other: "SearchResult", keep_duplicates: bool = False) -> "SearchResult":
        copy = deepcopy(self)
        for page in other._pages:
            copy.add(page=page, keep_duplicates=keep_duplicates)

        return copy

    def groupby(self, field: str) -> Dict[str, Any]:
        """
        group matched features by provided field name

        * STAC items not containing the respective field will returned as part of 'unknown' key
        * non-hashable fields (lists, sets) are '-'.joined (e.g. polarizations = ["HH", "HV"] -> "HH-HV")
        """

        if field not in ALL_SUPPORTED_GROUPBY_FIELDS:
            logger.warning(
                f"groupby(field='{field}') not supported - using '{UNKNOWN_GROUPBY_FIELD}' as value - supported: {', '.join(ALL_SUPPORTED_GROUPBY_FIELDS)}"
            )

        features_by_field = defaultdict(list)
        for feature in self._features:
            value = _get_safe_field_value(field=field, stac_item=feature)
            features_by_field[value].append(feature)

        return dict(features_by_field)


def _get_safe_field_value(field: str, stac_item: Dict[str, Any]):
    if field in ROOT_LEVEL_GROUPBY_FIELDS:
        return stac_item[field]

    target_field = STAC_PREFIXED_BY_QUERY_FIELDS.get(field, field)
    try:
        value = stac_item["properties"][target_field]
    except KeyError:
        value = UNKNOWN_GROUPBY_FIELD

    try:
        hash(value)
    except TypeError:
        value = "-".join(value)
    return value


class StacSearch:
    def __init__(self, session: CapellaConsoleSession, **kwargs) -> None:
        cur_kwargs = deepcopy(kwargs)
        self.session = session
        self.payload: Dict[str, Any] = {}
        self.threaded = cur_kwargs.pop("threaded", False)

        sortby = cur_kwargs.pop("sortby", None)
        if sortby:
            self.payload["sortby"] = self._get_sort_payload(sortby)

        ownership_option = cur_kwargs.pop("ownership", None)
        if OwnershipOption.is_valid(ownership_option):
            self.payload["ownership"] = ownership_option

        query_payload = self._get_query_payload(cur_kwargs)
        if query_payload:
            self.payload["query"] = dict(query_payload)

        if "limit" not in self.payload:
            self.payload["limit"] = CATALOG_DEFAULT_LIMIT

        if self.payload["limit"] > STAC_MAX_ITEM_RETURN:
            logger.warning(
                f"Capella's STAC server can return up to {STAC_MAX_ITEM_RETURN} items ({self.payload['limit']} requested), limiting to that"
            )
            self.payload["limit"] = STAC_MAX_ITEM_RETURN

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
        if not self.threaded:
            return self._fetch_all_sync()
        else:
            return self._fetch_all_threaded()

    def _fetch_all_sync(self):
        search_result = SearchResult(request_body=self.payload)
        cur_payload = deepcopy(self.payload)

        # limit page size
        cur_payload["limit"] = min(CATALOG_MAX_PAGE_SIZE, self.payload["limit"])

        page_cnt = 1
        next_href = None

        while True:
            start = len(search_result)
            end = min(start + cur_payload["limit"], self.payload["limit"])
            _log_page_query(page_cnt=page_cnt, start=start, end=end)

            # safeguard to not step over 10000
            if start + cur_payload["limit"] > STAC_MAX_ITEM_RETURN:
                # translate limit/ page for last request
                missing = STAC_MAX_ITEM_RETURN - len(search_result)
                if not missing:
                    break

                cur_payload["limit"] = missing
                cur_payload["page"] = int(len(search_result) / missing) + 1

            page_data = _page_search(self.session, cur_payload, next_href)
            number_matched = page_data["numberMatched"]
            items_added = search_result.add(page_data)

            limit_reached = len(search_result) >= self.payload["limit"] or len(search_result) >= number_matched

            # all dupes
            size_unchanged = items_added == 0
            if limit_reached or size_unchanged:
                break

            next_href = _get_next_page_href(page_data)
            if next_href is None:
                break

            if page_cnt == 1:
                logger.info(f"Matched a total of {number_matched} stac items - returning up to {self.payload['limit']}")

            page_cnt += 1
            cur_payload["page"] = page_cnt

        search_result._truncate()
        search_result._report()
        return search_result

    def _fetch_all_threaded(self):
        search_result = SearchResult(request_body=self.payload)
        page_payloads = self._get_page_payloads()

        # TODO: configurable max threads
        with ThreadPoolExecutor(max_workers=len(page_payloads)) as executor:
            results = executor.map(_page_search, repeat(self.session), page_payloads)

        for page in results:
            search_result.add(page)

        search_result._truncate()
        search_result._report()
        return search_result

    def _get_page_payloads(self) -> List[Dict[str, Any]]:
        # ping for how many matches in total
        cur_payload = {**self.payload, "limit": 1}
        single_match_page = _page_search(self.session, cur_payload)
        number_matched = single_match_page["numberMatched"]

        num_pages = ceil(min(number_matched, self.payload["limit"]) / CATALOG_MAX_PAGE_SIZE)
        logger.info(
            f"Matched a total of {number_matched} stac items - fetching in {num_pages} parallel requests (page size {CATALOG_MAX_PAGE_SIZE}) - returning up to {self.payload['limit']}"
        )

        payloads = [
            {**self.payload, "limit": min(CATALOG_MAX_PAGE_SIZE, self.payload["limit"]), "page": i}
            for i in range(1, num_pages + 1)
        ]

        # safeguard to not step over 10000
        overflow = payloads[-1]["limit"] * payloads[-1]["page"] > STAC_MAX_ITEM_RETURN
        if overflow:
            offset = payloads[-1]["limit"] * payloads[-2]["page"]
            missing = STAC_MAX_ITEM_RETURN - offset
            payloads[-1]["limit"] = missing
            payloads[-1]["page"] = int(offset / missing) + 1

        return payloads


def _log_page_query(page_cnt: int, start: int, end: int):
    if page_cnt != 1:
        logger.info(f"\tpage {page_cnt} ({start} - {end})")


def _get_next_page_href(page_data: Dict[str, Any]) -> Optional[str]:
    links = page_data.get("links", [])
    try:
        next_href: Optional[str] = next(filter(lambda c: c["rel"] == "next", links))["href"]
    except StopIteration:
        next_href = None

    return next_href


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

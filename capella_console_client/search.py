from copy import deepcopy
from functools import partial, wraps
from typing import Any, ClassVar, DefaultDict
from collections.abc import Callable
from collections import defaultdict
from urllib.parse import urlparse
from dataclasses import dataclass, field
from math import ceil
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from abc import ABCMeta, abstractmethod

from capella_console_client.logconf import logger
from capella_console_client.report import print_task_search_result
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.config import (
    STAC_ALL_SUPPORTED_SEARCH_FIELDS,
    STAC_ALL_SUPPORTED_SORTBY,
    STAC_SUPPORTED_ROOT_FIELDS,
    STAC_SUPPORTED_QUERY_FIELDS,
    STAC_PREFIXED_BY_QUERY_FIELDS,
    QUERY_OPERATORS,
    CATALOG_MAX_PAGE_SIZE,
    CATALOG_DEFAULT_LIMIT,
    CATALOG_STAC_MAX_ITEM_RETURN,
    STAC_ALL_SUPPORTED_GROUPBY_FIELDS,
    STAC_ROOT_LEVEL_GROUPBY_FIELDS,
    SUPPORTED_TASKING_REQUEST_SEARCH_QUERY_FIELDS,
    TR_FILTERS_BY_QUERY_FIELDS,
    TR_MAX_CONCURRENCY,
    TR_SEARCH_DEFAULT_PAGE_SIZE,
    TR_SUPPORTED_GROUPBY_FIELDS,
    UNKNOWN_GROUPBY_FIELD,
    SUPPORTED_RR_SEARCH_QUERY_FIELDS,
    RR_FILTERS_BY_QUERY_FIELDS,
    RR_SUPPORTED_GROUPBY_FIELDS,
)
from capella_console_client.enumerations import (
    CollectionTier,
    CollectionType,
    OwnershipOption,
    TaskingRequestStatus,
    BaseEnum,
    RepeatCollectionTier,
)
from capella_console_client.validate import _compact_unique, _validate_uuids


class SearchEntity(str, BaseEnum):
    STAC_ITEM = "STAC item"
    TASKING_REQUEST = "tasking request"
    REPEAT_REQUEST = "repeat request"


class Groupby(metaclass=ABCMeta):
    ROOT_GROUPBY_FIELDS: ClassVar[set[str]] = NotImplemented
    PROPERTIES_GROUPBY_FIELDS: ClassVar[set[str]] = NotImplemented

    @property
    def supported_fields(self):
        return self.ROOT_GROUPBY_FIELDS | self.PROPERTIES_GROUPBY_FIELDS

    def groupby(self, features, field: str) -> dict[str, Any]:
        """
        group matched features by provided field name

        * items not containing the respective field will returned as part of 'unknown' key
        * non-hashable fields (lists, sets) are '-'.joined (e.g. polarizations = ["HH", "HV"] -> "HH-HV")
        """

        if field not in self.supported_fields:
            logger.warning(
                f"groupby(field='{field}') not supported - using '{UNKNOWN_GROUPBY_FIELD}' as value - supported: {', '.join(self.supported_fields)}"
            )

        features_by_field = defaultdict(list)
        for feature in features:
            value = self._get_safe_field_value(field=field, item=feature)
            features_by_field[value].append(feature)

        return dict(features_by_field)

    @abstractmethod
    def _get_safe_field_value(self, field: str, item: dict[str, Any]):
        pass


@dataclass
class SearchResult(metaclass=ABCMeta):
    request_body: dict[str, Any] = field(default_factory=dict)
    _pages: list[dict[str, Any]] = field(default_factory=list)
    _features: list[dict[str, Any]] = field(default_factory=list)

    grouper: ClassVar[Groupby] = NotImplemented

    def _truncate(self):
        len_features = len(self)
        requested_limit = self.request_body.get("limit")
        if requested_limit and len_features > requested_limit:
            self._features = self._features[:requested_limit]

    def _report(self):
        len_results = len(self)
        if not len_results:
            message = f"found no {self.entity.value}s matching your query"
        else:
            message = f"found {len_results} {self.entity.value}{self.multiple_suffix}"
        logger.info(message)

    @property
    def multiple_suffix(self):
        len_results = len(self)
        return "s" if len_results > 1 else ""

    # backwards compatibility
    def __getitem__(self, key):
        return self._features.__getitem__(key)

    def __iter__(self):
        return self._features.__iter__()

    def __len__(self):
        return len(self._features)

    def to_feature_collection(self):
        return {"type": "FeatureCollection", "features": self._features}

    @abstractmethod
    def add(self, page: dict[str, Any], keep_duplicates: bool = False) -> int:
        pass

    def merge(self, other: "SearchResult", keep_duplicates: bool = False) -> "SearchResult":
        copy = deepcopy(self)
        for page in other._pages:
            copy.add(page=page, keep_duplicates=keep_duplicates)

        return copy

    def groupby(self, field: str) -> dict[str, Any]:
        """
        group matched features by provided field name

        * items not containing the respective field will returned as part of 'unknown' key
        * non-hashable fields (lists, sets) are '-'.joined
        """
        return self.grouper.groupby(field=field, features=self._features)


class StacGroupby(Groupby):

    ROOT_GROUPBY_FIELDS: ClassVar[set[str]] = STAC_ROOT_LEVEL_GROUPBY_FIELDS
    PROPERTIES_GROUPBY_FIELDS: ClassVar[set[str]] = STAC_SUPPORTED_QUERY_FIELDS

    def _get_safe_field_value(self, field: str, item: dict[str, Any]):
        if field in STAC_ROOT_LEVEL_GROUPBY_FIELDS:
            return item[field]

        target_field = STAC_PREFIXED_BY_QUERY_FIELDS.get(field, field)
        try:
            value = item["properties"][target_field]
        except KeyError:
            value = UNKNOWN_GROUPBY_FIELD

        try:
            hash(value)
        except TypeError:
            value = "-".join(value)
        return value


class StacSearchResult(SearchResult):
    entity: SearchEntity = SearchEntity.STAC_ITEM
    grouper: ClassVar[Groupby] = StacGroupby()

    def __repr__(self):
        return f"{self.__class__} ({len(self)} {self.entity.value}{self.multiple_suffix})"

    @property
    def stac_ids(self):
        return [item["id"] for item in self._features]

    @property
    def collect_ids(self):
        return [item["properties"].get("capella:collect_id", "N/A") for item in self._features]

    def add(self, page: dict[str, Any], keep_duplicates: bool = False) -> int:
        if not keep_duplicates:
            page = self._filter_dupes(page)
        self._pages.append(page)
        self._features.extend(page["features"])
        return len(page["features"])

    def _filter_dupes(self, page: dict[str, Any]) -> dict[str, Any]:
        # drop duplicates within page features
        page_stac_ids = [feat["id"] for feat in page["features"]]
        set_page_stac_ids = set(page_stac_ids)

        if len(set_page_stac_ids) != len(page["features"]):
            page["features"] = [page["features"][page_stac_ids.index(p_id)] for p_id in set_page_stac_ids]

        # drop duplicates within StacSearchResult
        dupes = set_page_stac_ids.intersection(self.stac_ids)

        if dupes:
            page["features"] = [p for p in page["features"] if p["id"] not in dupes]

        return page


class TaskingRequestGroupby(Groupby):

    ROOT_GROUPBY_FIELDS: ClassVar[set[str]] = set()
    PROPERTIES_GROUPBY_FIELDS: ClassVar[set[str]] = TR_SUPPORTED_GROUPBY_FIELDS

    def _get_safe_field_value(self, field: str, item: dict[str, Any]):
        if field in self.ROOT_GROUPBY_FIELDS:
            return item[field]

        try:
            value = item["properties"][field]
        except KeyError:
            value = UNKNOWN_GROUPBY_FIELD

        try:
            hash(value)
        except TypeError:
            value = "-".join(value)
        return value


class RepeatRequestGroupby(TaskingRequestGroupby):
    ROOT_GROUPBY_FIELDS: ClassVar[set[str]] = set()
    PROPERTIES_GROUPBY_FIELDS: ClassVar[set[str]] = RR_SUPPORTED_GROUPBY_FIELDS


class TaskingRequestSearchResult(SearchResult):
    entity: SearchEntity = SearchEntity.TASKING_REQUEST
    grouper: ClassVar[Groupby] = TaskingRequestGroupby()

    def __repr__(self):
        return f"{self.__class__} ({len(self)} {self.entity.value}{self.multiple_suffix})"

    @property
    def tasking_request_ids(self):
        return [item["properties"]["taskingrequestId"] for item in self._features]

    @property
    def repeat_request_ids(self):
        return [item["properties"].get("repeatrequestId", "N/A") for item in self._features]

    def add(self, page: dict[str, Any], keep_duplicates: bool = False) -> int:
        self._pages.append(page)
        self._features.extend(page["results"])
        return len(page["results"])


class RepeatRequestSearchResult(SearchResult):
    entity: SearchEntity = SearchEntity.REPEAT_REQUEST
    grouper: ClassVar[Groupby] = RepeatRequestGroupby()

    def __repr__(self):
        return f"{self.__class__} ({len(self)} {self.entity.value}{self.multiple_suffix})"

    @property
    def repeat_request_ids(self):
        return [item["properties"]["repeatrequestId"] for item in self._features]

    def add(self, page: dict[str, Any], keep_duplicates: bool = False) -> int:
        self._pages.append(page)
        self._features.extend(page["results"])
        return len(page["results"])


class AbstractSearch(metaclass=ABCMeta):

    @abstractmethod
    def _get_query_payload(self, kwargs) -> dict[str, Any]:
        pass

    @abstractmethod
    def _get_sort_payload(self, sortby):
        pass

    def _split_op(self, cur_field: str) -> tuple[str, str]:
        parts = cur_field.split("__")
        if len(parts) == 2:
            op = parts[1]
        else:
            op = "eq"
        return (parts[0], op)

    @abstractmethod
    def fetch_all(self) -> SearchResult:
        pass


class StacSearch(AbstractSearch):
    def __init__(self, session: CapellaConsoleSession, **kwargs) -> None:
        cur_kwargs = deepcopy(kwargs)
        self.session = session
        self.payload: dict[str, Any] = {}
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

        if self.payload["limit"] > CATALOG_STAC_MAX_ITEM_RETURN:
            logger.warning(
                f"Capella's STAC server can return up to {CATALOG_STAC_MAX_ITEM_RETURN} items ({self.payload['limit']} requested), limiting to that"
            )
            self.payload["limit"] = CATALOG_STAC_MAX_ITEM_RETURN

    def _get_query_payload(self, kwargs) -> DefaultDict[str, dict[str, Any]]:
        query_payload: DefaultDict[str, dict[str, Any]] = defaultdict(dict)

        for cur_field, value in kwargs.items():
            cur_field, op = self._split_op(cur_field)
            if cur_field not in STAC_ALL_SUPPORTED_SEARCH_FIELDS:
                logger.warning(f"filter {cur_field} not supported ... omitting")
                continue

            if op not in QUERY_OPERATORS:
                logger.warning(f"operator {op} not supported ... omitting")
                continue

            if cur_field in STAC_SUPPORTED_ROOT_FIELDS:
                self.payload[cur_field] = value
            elif cur_field in STAC_SUPPORTED_QUERY_FIELDS:
                if type(value) == list:
                    op = "in"

                target_field = STAC_PREFIXED_BY_QUERY_FIELDS.get(cur_field, cur_field)
                query_payload[target_field][op] = value

        return query_payload

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

            if field not in STAC_ALL_SUPPORTED_SORTBY:
                logger.warning(f"sorting by {field} not supported ... omitting")
                continue

            if field in STAC_SUPPORTED_QUERY_FIELDS or field == "datetime":
                field = f"properties.{field}"

            sorts.append({"field": field, "direction": directions[direction]})
        return sorts

    def fetch_all(self) -> StacSearchResult:
        logger.info(f"searching catalog with payload {self.payload}")
        if not self.threaded:
            return self._fetch_all_sync()
        else:
            return self._fetch_all_threaded()

    def _fetch_all_sync(self):
        search_result = StacSearchResult(request_body=self.payload)
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
            if start + cur_payload["limit"] > CATALOG_STAC_MAX_ITEM_RETURN:
                # translate limit/ page for last request
                missing = CATALOG_STAC_MAX_ITEM_RETURN - len(search_result)
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
        search_result = StacSearchResult(request_body=self.payload)
        page_payloads = self._get_page_payloads()

        # TODO: configurable max threads
        with ThreadPoolExecutor(max_workers=len(page_payloads)) as executor:
            results = executor.map(_page_search, repeat(self.session), page_payloads)

        for page in results:
            search_result.add(page)

        search_result._truncate()
        search_result._report()
        return search_result

    def _get_page_payloads(self) -> list[dict[str, Any]]:
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
        overflow = payloads[-1]["limit"] * payloads[-1]["page"] > CATALOG_STAC_MAX_ITEM_RETURN
        if overflow:
            offset = payloads[-1]["limit"] * payloads[-2]["page"]
            missing = CATALOG_STAC_MAX_ITEM_RETURN - offset
            payloads[-1]["limit"] = missing
            payloads[-1]["page"] = int(offset / missing) + 1

        return payloads


def _log_page_query(page_cnt: int, start: int, end: int):
    if page_cnt != 1:
        logger.info(f"\tpage {page_cnt} ({start} - {end})")


def _get_next_page_href(page_data: dict[str, Any]) -> str | None:
    links = page_data.get("links", [])
    try:
        next_href: str | None = next(filter(lambda c: c["rel"] == "next", links))["href"]
    except StopIteration:
        next_href = None

    return next_href


def _page_search(session: CapellaConsoleSession, payload: dict[str, Any], next_href: str = None) -> dict[str, Any]:
    if next_href:
        # STAC API to return normalized asset hrefs, not api gateway - fixing this here ...
        url_parsed = urlparse(next_href)
        if url_parsed.netloc != urlparse(session.search_url).netloc:
            next_href = f"{session.search_url}?{url_parsed.query}"

    url = session.search_url if next_href is None else next_href
    resp = session.post(url, json=payload)

    data: dict[str, Any] = resp.json()
    return data


class AbstractQuerySanitizer(metaclass=ABCMeta):
    SUPPORTED: set[str] = set()

    @staticmethod
    def single_or_list(func: Callable[..., list[Any]]) -> Callable[..., list[Any] | Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> list[Any] | Any:
            if not isinstance(kwargs["value"], str):
                return func(args[0], **kwargs)

            kwargs["value"] = [kwargs["value"]]
            result = func(args[0], **kwargs)
            if result is None:
                return None
            return result[0]

        return wrapper

    @classmethod
    def has_sanitizer(cls, field) -> bool:
        return field in cls.SUPPORTED

    def _sanitize_collection_type(self, field, value):
        return self._sanitize_enum(field=field, value=value, enum_cls=CollectionType)

    @single_or_list
    def _sanitize_enum(self, field, value, enum_cls):
        valid_status = [s.lower() for s in value if s.lower() in enum_cls]

        if not valid_status:
            logger.warning(f"No valid {field} provided ({value}) ... dropping from filter")
            return None

        return valid_status

    @single_or_list
    def _sanitize_uuids(self, field, value):
        value = _compact_unique(value)
        _validate_uuids(value)
        return value

    def _sanitize_status(self, field, value):
        return self._sanitize_enum(field=field, value=value, enum_cls=TaskingRequestStatus)

    def sanitize(self, field, value):
        if not self.has_sanitizer(field):
            return value

        sanitizer_rules = {
            "collection_type": self._sanitize_collection_type,
            "status": self._sanitize_status,
        }

        sanitizer_rules.update(self._get_custom_sanitizer_rules())

        return sanitizer_rules[field](field=field, value=value)

    @abstractmethod
    def _get_custom_sanitizer_rules(self):
        pass


class TaskingRequestQuerySanitizer(AbstractQuerySanitizer):

    SUPPORTED = {"collection_tier", "collection_type", "status", "tasking_request_id"}

    def _get_custom_sanitizer_rules(self):
        return {
            "collection_tier": self._sanitize_collection_tier,
            "tasking_request_id": self._sanitize_uuids,
        }

    def _sanitize_collection_tier(self, field, value):
        return self._sanitize_enum(field=field, value=value, enum_cls=CollectionTier)


class RepeatRequestQuerySanitizer(AbstractQuerySanitizer):

    SUPPORTED = {"collection_tier", "collection_type", "status", "repeat_request_id"}

    def _get_custom_sanitizer_rules(self):
        return {
            "collection_tier": self._sanitize_collection_tier,
            "repeat_request_id": self._sanitize_uuids,
        }

    def _sanitize_collection_tier(self, field, value):
        return self._sanitize_enum(field=field, value=value, enum_cls=RepeatCollectionTier)


def _fetch_page(params, session, search_endpoint, search_entity, search_payload):
    resp = session.post(search_endpoint, params=params, json=search_payload)
    page = resp.json()
    if page["currentPage"] > 1:
        logger.info(f"page {page['currentPage']} out of {page['totalPages']}: {len(page['results'])} {search_entity}")
    return page


class AbstractTaskRepeatSearch(AbstractSearch):

    SEARCH_ENTITY: SearchEntity
    SEARCH_ENDPOINT: str
    QUERY_PAYLOAD_FIELD: str
    SUPPORTED_QUERY_FIELDS: set[str]
    FILTERS_BY_QUERY_FIELDS: dict[str, str]
    QUERY_SANITIZER_CLS: type[AbstractQuerySanitizer]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        required_class_vars = {
            "SEARCH_ENTITY",
            "SEARCH_ENDPOINT",
            "QUERY_PAYLOAD_FIELD",
            "SUPPORTED_QUERY_FIELDS",
            "FILTERS_BY_QUERY_FIELDS",
            "QUERY_SANITIZER_CLS",
        }

        missing_required = [req for req in required_class_vars if not hasattr(cls, req)]

        if missing_required:
            raise TypeError(f"{cls.__name__} must define {', '.join(missing_required)}")

    def __init__(self, session: CapellaConsoleSession, **kwargs) -> None:
        self.session = session
        self.payload: dict[str, Any] = {}
        self.page_size = kwargs.pop("page_size", None) or TR_SEARCH_DEFAULT_PAGE_SIZE
        self.threaded = kwargs.pop("threaded", True)
        # TODO: max results (limit)

        query_payload = self._get_query_payload(kwargs)
        if query_payload:
            self.payload[self.QUERY_PAYLOAD_FIELD] = dict(query_payload)

        # sortby = cur_kwargs.pop("sortby", None)
        # if sortby:
        #     self.payload["sortby"] = self._get_sort_payload(sortby)

    def _get_sort_payload(self, sortby):
        raise RuntimeError("Not implemented")

    def _get_query_payload(self, kwargs) -> dict[str, Any]:
        query_payload: dict[str, Any] = defaultdict(dict)

        if self.SEARCH_ENTITY == SearchEntity.TASKING_REQUEST:
            query_payload["includeRepeatingTasks"] = {"eq": False}

        for_org = kwargs.pop("for_org", False)
        query_payload = self._add_user_org_query(query_payload, for_org, **kwargs)

        sntzr = self.QUERY_SANITIZER_CLS()

        for cur_field, value in kwargs.items():
            cur_field, op = self._split_op(cur_field)
            if cur_field not in self.SUPPORTED_QUERY_FIELDS:
                logger.warning(f"filter {cur_field} not supported ... omitting")
                continue

            if op not in QUERY_OPERATORS:
                logger.warning(f"operator {op} not supported ... omitting")
                continue

            target_field = self.FILTERS_BY_QUERY_FIELDS.get(cur_field, cur_field)

            if sntzr.has_sanitizer(cur_field):
                value = sntzr.sanitize(field=cur_field, value=value)

            # op == in currently not supported by api
            # TODO: replace direct assignment (no operator) once in supported
            if isinstance(value, list):
                query_payload[target_field] = value
                continue

            query_payload[target_field][op] = value

        return query_payload

    def _add_user_org_query(self, query_payload, for_org, **kwargs):
        # TODO: resellerId?
        any_of = ("org_id", "user_id")

        if any(x in kwargs for x in any_of):
            return query_payload

        if not self.session.customer_id or not self.session.organization_id:
            self.session._cache_user_info()

        if for_org:
            query_payload["organizationIds"] = [self.session.organization_id]
            return query_payload

        # TODO: should the endpoint fill this in?
        query_payload["userId"] = self.session.customer_id
        return query_payload

    def fetch_all(self) -> TaskingRequestSearchResult | RepeatRequestSearchResult:
        search_result = self._init_search_result()
        logger.info(f"searching {self.SEARCH_ENTITY.value}s with payload {self.payload}")
        first_page = _fetch_page(
            params={"page": 1, "limit": self.page_size},
            session=self.session,
            search_endpoint=self.SEARCH_ENDPOINT,
            search_entity=self.SEARCH_ENTITY,
            search_payload=self.payload,
        )

        total_pages = first_page["totalPages"]
        fetch_more = total_pages > 1

        search_result.add(first_page)
        if not fetch_more:
            print_task_search_result(search_result._features, search_entity=self.SEARCH_ENTITY.value)
            return search_result

        page_params = [{"page": i, "limit": self.page_size} for i in range(2, total_pages + 1)]

        _fetch_worker = partial(
            _fetch_page,
            session=self.session,
            search_endpoint=self.SEARCH_ENDPOINT,
            search_entity=self.SEARCH_ENTITY,
            search_payload=self.payload,
        )

        if self.threaded:
            with ThreadPoolExecutor(max_workers=TR_MAX_CONCURRENCY) as executor:
                results = executor.map(_fetch_worker, page_params)

            for page in results:
                search_result.add(page)
        else:
            for params in page_params:
                page = _fetch_worker(params)
                search_result.add(page)

        print_task_search_result(search_result._features, search_entity=self.SEARCH_ENTITY.value)
        return search_result

    @abstractmethod
    def _init_search_result(self) -> TaskingRequestSearchResult | RepeatRequestSearchResult:
        pass


class TaskingRequestSearch(AbstractTaskRepeatSearch):

    SEARCH_ENTITY = SearchEntity.TASKING_REQUEST
    SEARCH_ENDPOINT = "/tasks/search"
    QUERY_PAYLOAD_FIELD = "query"
    SUPPORTED_QUERY_FIELDS = SUPPORTED_TASKING_REQUEST_SEARCH_QUERY_FIELDS
    FILTERS_BY_QUERY_FIELDS = TR_FILTERS_BY_QUERY_FIELDS
    QUERY_SANITIZER_CLS: type[AbstractQuerySanitizer] = TaskingRequestQuerySanitizer

    def _init_search_result(self) -> TaskingRequestSearchResult:
        return TaskingRequestSearchResult(request_body=self.payload)


class RepeatRequestSearch(AbstractTaskRepeatSearch):

    SEARCH_ENTITY = SearchEntity.REPEAT_REQUEST
    SEARCH_ENDPOINT = "/repeat-requests/search"
    QUERY_PAYLOAD_FIELD = "filter"
    SUPPORTED_QUERY_FIELDS = SUPPORTED_RR_SEARCH_QUERY_FIELDS
    FILTERS_BY_QUERY_FIELDS = RR_FILTERS_BY_QUERY_FIELDS
    QUERY_SANITIZER_CLS = RepeatRequestQuerySanitizer

    def _init_search_result(self) -> RepeatRequestSearchResult:
        return RepeatRequestSearchResult(request_body=self.payload)

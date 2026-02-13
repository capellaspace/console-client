import pytest

from capella_console_client.search import StacSearchResult
from capella_console_client.config import (
    STAC_ROOT_LEVEL_GROUPBY_FIELDS,
)

from .test_data import (
    get_canned_search_results_single_page,
    get_canned_search_results_with_collect_id,
    MOCK_GROUPBY_STAC_ITEM,
)


def test_search_result_add_drops_dupes():
    page = get_canned_search_results_single_page()
    result = StacSearchResult()
    added = result.add(page)
    assert added == len(page["features"])
    orig_len = len(result)

    # all dupes -> all filtered
    added = result.add(page)
    assert added == 0
    assert orig_len == len(result)


def test_search_result_add_drops_keep_dupes():
    page = get_canned_search_results_single_page()
    result = StacSearchResult()
    added = result.add(page)
    assert added == len(page["features"])
    added = result.add(page, keep_duplicates=True)
    assert added == len(page["features"])
    assert len(result) == 2 * len(page["features"])


def test_search_result_merge_dupes():
    page = get_canned_search_results_single_page()
    result1 = StacSearchResult()
    result1.add(page)

    result2 = StacSearchResult()
    result2.add(page)

    orig_len1 = len(result1)
    orig_len2 = len(result2)
    merged = result1.merge(result2)

    assert len(merged) == len(result1)
    assert orig_len1 == len(result1)
    assert orig_len2 == len(result2)


def test_search_result_merge_keep():
    page = get_canned_search_results_single_page()
    result1 = StacSearchResult()
    result1.add(page)

    result2 = StacSearchResult()
    result2.add(page)

    orig_len1 = len(result1)
    orig_len2 = len(result2)
    merged = result1.merge(result2, keep_duplicates=True)

    assert len(merged) == len(result1) + len(result2)
    assert orig_len1 == len(result1)
    assert orig_len2 == len(result2)


def test_search_result_has_collect_ids():
    result1 = StacSearchResult()
    page = get_canned_search_results_with_collect_id()
    result1.add(page)
    assert len(result1.collect_ids) == len(page["features"])


def test_search_result_groupby_empty():
    empty = StacSearchResult()
    assert empty.groupby(field="id") == {}


@pytest.mark.parametrize("field", ["email", "pw", "other", "field", "that", "does", "not", "exist"])
def test_search_result_groupby_invalid_field(field):
    result = StacSearchResult(_features=get_canned_search_results_with_collect_id()["features"])
    ret = result.groupby(field=field)
    assert list(ret.keys()) == ["unknown"]


@pytest.mark.parametrize("field", [*STAC_ROOT_LEVEL_GROUPBY_FIELDS, *MOCK_GROUPBY_STAC_ITEM["properties"].keys()])
def test_search_result_groupby_known_field(field):
    result = StacSearchResult(_features=[MOCK_GROUPBY_STAC_ITEM])
    ret = result.groupby(field=field)
    assert len(ret) == 1
    assert isinstance(ret, dict)
    assert list(ret.values()) == [[MOCK_GROUPBY_STAC_ITEM]]


@pytest.mark.parametrize("field", ["epsg", "billable_area"])
def test_search_result_groupby_missing_field(field):
    result = StacSearchResult(_features=[MOCK_GROUPBY_STAC_ITEM])
    ret = result.groupby(field=field)
    assert list(ret.keys()) == ["unknown"]
    assert list(ret.values()) == [[MOCK_GROUPBY_STAC_ITEM]]

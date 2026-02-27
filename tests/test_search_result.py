import pytest

from capella_console_client.search import (
    StacSearchResult,
    TaskingRequestSearchResult,
    RepeatRequestSearchResult,
)
from capella_console_client.config import (
    STAC_ROOT_LEVEL_GROUPBY_FIELDS,
    TR_SUPPORTED_GROUPBY_FIELDS,
    RR_SUPPORTED_GROUPBY_FIELDS,
)

from .test_data import (
    get_canned_search_results_single_page,
    get_canned_search_results_with_collect_id,
    MOCK_GROUPBY_STAC_ITEM,
    TASK_1,
    TASK_2,
    REPEAT_REQUEST_1,
    REPEAT_REQUEST_2,
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


# TaskingRequestSearchResult groupby tests


def test_tasking_request_search_result_groupby_empty():
    empty = TaskingRequestSearchResult()
    assert empty.groupby(field="taskingrequestId") == {}


@pytest.mark.parametrize("field", ["email", "pw", "other", "field", "that", "does", "not", "exist"])
def test_tasking_request_search_result_groupby_invalid_field(field):
    result = TaskingRequestSearchResult(_features=[TASK_1, TASK_2])
    ret = result.groupby(field=field)
    assert list(ret.keys()) == ["unknown"]
    assert ret["unknown"] == [TASK_1, TASK_2]


@pytest.mark.parametrize("field", TR_SUPPORTED_GROUPBY_FIELDS)
def test_tasking_request_search_result_groupby_known_field(field):
    """Test groupby with all supported fields using TASK_1"""
    result = TaskingRequestSearchResult(_features=[TASK_1])
    ret = result.groupby(field=field)
    assert len(ret) == 1
    assert isinstance(ret, dict)
    # All features should be grouped (either under a value or "unknown" if field is missing)
    assert sum(len(v) for v in ret.values()) == 1


def test_tasking_request_search_result_groupby_missing_field():
    """Test groupby when field is supported but missing from the feature"""
    # customAttribute1 is in TR_SUPPORTED_GROUPBY_FIELDS but not set in TASK_1/TASK_2
    result = TaskingRequestSearchResult(_features=[TASK_1, TASK_2])
    ret = result.groupby(field="customAttribute1")
    assert list(ret.keys()) == ["unknown"]
    assert ret["unknown"] == [TASK_1, TASK_2]


@pytest.mark.parametrize(
    "field,expected_groups,expected_values",
    [
        ("taskingrequestId", 2, {"abc": [TASK_1], "def": [TASK_2]}),
        ("collectionTier", 1, {"7_day": [TASK_1, TASK_2]}),
        ("userId", 1, {"MOCK_ID": [TASK_1, TASK_2]}),
    ],
)
def test_tasking_request_search_result_groupby_scenarios(field, expected_groups, expected_values):
    """Test groupby with various fields and expected grouping outcomes"""
    result = TaskingRequestSearchResult(_features=[TASK_1, TASK_2])
    ret = result.groupby(field=field)
    assert len(ret) == expected_groups
    assert ret == expected_values


# RepeatRequestSearchResult groupby tests


def test_repeat_request_search_result_groupby_empty():
    empty = RepeatRequestSearchResult()
    assert empty.groupby(field="repeatrequestId") == {}


@pytest.mark.parametrize("field", ["email", "pw", "other", "field", "that", "does", "not", "exist"])
def test_repeat_request_search_result_groupby_invalid_field(field):
    result = RepeatRequestSearchResult(_features=[REPEAT_REQUEST_1, REPEAT_REQUEST_2])
    ret = result.groupby(field=field)
    assert list(ret.keys()) == ["unknown"]
    assert ret["unknown"] == [REPEAT_REQUEST_1, REPEAT_REQUEST_2]


@pytest.mark.parametrize("field", RR_SUPPORTED_GROUPBY_FIELDS)
def test_repeat_request_search_result_groupby_known_field(field):
    """Test groupby with all supported fields using REPEAT_REQUEST_1"""
    result = RepeatRequestSearchResult(_features=[REPEAT_REQUEST_1])
    ret = result.groupby(field=field)
    assert len(ret) == 1
    assert isinstance(ret, dict)
    # All features should be grouped (either under a value or "unknown" if field is missing)
    assert sum(len(v) for v in ret.values()) == 1


def test_repeat_request_search_result_groupby_missing_field():
    """Test groupby when field is supported but missing from the feature"""
    # contractId is in RR_SUPPORTED_GROUPBY_FIELDS but not set in REPEAT_REQUEST_1/2
    result = RepeatRequestSearchResult(_features=[REPEAT_REQUEST_1, REPEAT_REQUEST_2])
    ret = result.groupby(field="contractId")
    assert list(ret.keys()) == ["unknown"]
    assert ret["unknown"] == [REPEAT_REQUEST_1, REPEAT_REQUEST_2]


@pytest.mark.parametrize(
    "field,expected_groups,expected_values",
    [
        ("repeatrequestId", 2, {"PANDA": [REPEAT_REQUEST_1], "BOAR": [REPEAT_REQUEST_2]}),
        ("collectionTier", 1, {"routine": [REPEAT_REQUEST_1, REPEAT_REQUEST_2]}),
        ("orgId", 1, {"PANDA_ORG": [REPEAT_REQUEST_1, REPEAT_REQUEST_2]}),
    ],
)
def test_repeat_request_search_result_groupby_scenarios(field, expected_groups, expected_values):
    """Test groupby with various fields and expected grouping outcomes"""
    result = RepeatRequestSearchResult(_features=[REPEAT_REQUEST_1, REPEAT_REQUEST_2])
    ret = result.groupby(field=field)
    assert len(ret) == expected_groups
    assert ret == expected_values

import pytest

from capella_console_client.sort import _sort_stac_items

TEST_CASES = [
    pytest.param(
        [{"id": 4}, {"id": 5}, {"id": 3}],
        [3, 4, 5],
        [{"id": 3}, {"id": 4}, {"id": 5}],
        id="sort",
    ),
    pytest.param(
        [{"id": 4}, {"id": 5}, {"id": 3}],
        [3, 4, 6],
        [{"id": 3}, {"id": 4}, {"id": 5}],
        id="single miss",
    ),
    pytest.param(
        [{"id": 4}, {"id": 5}, {"id": 3}],
        [2, 5, 6],
        [{"id": 5}, {"id": 4}, {"id": 3}],
        id="double miss",
    ),
    pytest.param(
        [{"id": 4}, {"id": 5}, {"id": 3}],
        [1, 8, 10],
        [{"id": 4}, {"id": 5}, {"id": 3}],
        id="all miss",
    ),
    pytest.param([], [], [], id="empty"),
]


@pytest.mark.parametrize("stac_items,stac_ids,sorted", TEST_CASES)
def test_sort_stac_items(stac_items, stac_ids, sorted):
    assert _sort_stac_items(stac_items, stac_ids) == sorted

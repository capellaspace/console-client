import pytest

from capella_console_client.validate import _validate_and_filter_stac_ids

TEST_CASES = [
    pytest.param(
        ["CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006"],
        ["CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006"],
        id="single",
    ),
    pytest.param(
        [
            "CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006",
            "CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006",
        ],
        ["CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006"],
        id="duplicate_filter",
    ),
    pytest.param(
        ["NOCAPELLA_C100_CPA_MO_CC_20220000000000_20220000000006"],
        [],
        id="non_valid_filter_single",
    ),
    pytest.param(
        [
            "CAPELLA_C100_SM_VS_HH_20220000000000_20220000000006",
            "CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006",
        ],
        ["CAPELLA_C99_SM_VS_HH_20220000000000_20220000000006"],
        id="non_valid_filter_single",
    ),
    pytest.param([], [], id="empty"),
]


@pytest.mark.parametrize("stac_ids,expected", TEST_CASES)
def test_validate_and_filter_stac_ids(stac_ids, expected):
    assert expected == _validate_and_filter_stac_ids(stac_ids)

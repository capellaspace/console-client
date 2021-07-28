import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.assets import (
    _get_asset_bytesize,
    _get_raster_href,
    _derive_stac_id,
    _derive_product_type,
)
from .test_data import MOCK_ASSET_HREF


def test_get_asset_bytesize(httpx_mock: HTTPXMock):
    httpx_mock.add_response(data="MOCK_CONTENT", headers={"Content-Length": "127"})

    bytesize = _get_asset_bytesize(MOCK_ASSET_HREF)
    assert bytesize == 127


@pytest.mark.parametrize("key", ["HH", "VV"])
def test_get_raster_href(key):
    assert (
        _get_raster_href(
            {
                key: {"href": MOCK_ASSET_HREF},
            }
        )
        == MOCK_ASSET_HREF
    )


def test_derive_stac_id():
    STAC_ID = "CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740"
    assert _derive_stac_id({"HH": {"href": STAC_ID}}) == STAC_ID


def test_derive_stac_id_invalid():
    with pytest.raises(ValueError):
        _derive_stac_id({"HH": {"href": "THIS_AINT_A_STAC_ID"}})


@pytest.mark.parametrize(
    "stac_id,expected",
    [
        ("CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740", "GEO"),
        ("CAPELLA_C05_SM_SLC_HH_20210727091736_20210727091740", "SLC"),
        ("CAPELLA_C05_SM_GEC_HH_20210727091736_20210727091740", "GEC"),
        ("CAPELLA_C05_SM_SICD_HH_20210727091736_20210727091740", "SICD"),
        ("CAPELLA_C05_SM_SIDD_HH_20210727091736_20210727091740", "SIDD"),
    ],
)
def test_derive_derive_product_type(stac_id, expected):
    HREF_TMPL = "https://test-data.capellaspace.com/capella-test/2021/1/19/{stac_id}/{stac_id}.png?AWSAccessKeyId=********&Expires=*****&Signature=******&x-amz-security-token=****"
    assert (
        _derive_product_type({"HH": {"href": HREF_TMPL.format(stac_id=stac_id)}})
        == expected
    )


def test_derive_derive_product_type_invalid():
    with pytest.raises(ValueError):
        _derive_product_type({"HH": {"href": "THIS_AINT_A_PRODUCT_TYPE"}})

from capella_console_client.assets import _get_asset_bytesize

from pytest_httpx import HTTPXMock

from .test_data import MOCK_ASSET_HREF


def test_get_asset_bytesize(httpx_mock: HTTPXMock):
    httpx_mock.add_response(data="MOCK_CONTENT", headers={"Content-Length": "127"})

    bytesize = _get_asset_bytesize(MOCK_ASSET_HREF)
    assert bytesize == 127

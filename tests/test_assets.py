import pytest
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch
from pytest_httpx import HTTPXMock
import time

from capella_console_client.assets import (
    _derive_stac_id,
    _fetch,
    DownloadRequest,
)


@pytest.fixture
def mock_sleep(monkeypatch):
    """Mock time.sleep to make tests run instantly without waiting for retry delays"""
    sleep_calls = []

    def _mock_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(time, "sleep", _mock_sleep)
    return sleep_calls


def test_derive_stac_id():
    STAC_ID = "CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740"
    assert _derive_stac_id({"HH": {"href": STAC_ID}}) == STAC_ID


def test_derive_stac_id_invalid():
    with pytest.raises(ValueError):
        _derive_stac_id({"HH": {"href": "THIS_AINT_A_STAC_ID"}})


def test_fetch_retry_on_http_status_error(httpx_mock: HTTPXMock, tmp_path: Path, mock_sleep):
    """Test that _fetch retries on HTTPStatusError and eventually succeeds"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    httpx_mock.add_response(status_code=500, text="Server Error")
    httpx_mock.add_response(status_code=500, text="Server Error")
    httpx_mock.add_response(status_code=200, text="SUCCESS_CONTENT")

    result = _fetch(dl_request, asset_size=100, show_progress=False, progress=MagicMock())

    assert result == local_path
    assert local_path.exists()
    assert local_path.read_text() == "SUCCESS_CONTENT"
    assert len(httpx_mock.get_requests()) == 3


def test_fetch_retry_timing(httpx_mock: HTTPXMock, tmp_path: Path, mock_sleep):
    """Test that _fetch uses exponential backoff (2s, 4s, 8s, up to 16s max)"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    httpx_mock.add_response(status_code=503, text="Service Unavailable")
    httpx_mock.add_response(status_code=503, text="Service Unavailable")
    httpx_mock.add_response(status_code=200, text="SUCCESS_CONTENT")

    result = _fetch(dl_request, asset_size=100, show_progress=False, progress=MagicMock())

    assert len(mock_sleep) == 2, f"Expected 2 sleep calls, got {len(mock_sleep)}"
    assert 1.8 <= mock_sleep[0] <= 2.2, f"First retry should wait ~2s, got {mock_sleep[0]:.2f}s"
    assert 3.8 <= mock_sleep[1] <= 4.2, f"Second retry should wait ~4s, got {mock_sleep[1]:.2f}s"

    assert result == local_path
    assert local_path.exists()


def test_fetch_retries_multiple_times(httpx_mock: HTTPXMock, tmp_path: Path, mock_sleep):
    """Test that _fetch retries multiple times before succeeding"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    for _ in range(4):
        httpx_mock.add_response(status_code=503, text="Service Unavailable")
    httpx_mock.add_response(status_code=200, text="SUCCESS_CONTENT")

    result = _fetch(dl_request, asset_size=100, show_progress=False, progress=MagicMock())

    assert result == local_path
    assert local_path.exists()
    assert local_path.read_text() == "SUCCESS_CONTENT"

    assert len(httpx_mock.get_requests()) == 5
    assert len(mock_sleep) == 4


def test_fetch_no_retry_on_success(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _fetch doesn't retry when request succeeds immediately"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    httpx_mock.add_response(status_code=200, text="SUCCESS_CONTENT")

    result = _fetch(dl_request, asset_size=100, show_progress=False, progress=MagicMock())

    assert result == local_path
    assert local_path.exists()
    assert local_path.read_text() == "SUCCESS_CONTENT"

    assert len(httpx_mock.get_requests()) == 1

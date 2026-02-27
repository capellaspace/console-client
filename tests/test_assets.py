import pytest
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch
from pytest_httpx import HTTPXMock
import time

from capella_console_client.assets import (
    _derive_stac_id,
    _fetch,
    _download_asset,
    DownloadRequest,
    progress_bar,
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


# Resume functionality tests


def test_fetch_resume_partial_download(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _fetch successfully resumes a partial download using 206 Partial Content"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create partial file (1000 bytes)
    local_path.write_bytes(b"A" * 1000)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    # Mock 206 response with remaining bytes
    httpx_mock.add_response(status_code=206, content=b"B" * 500, headers={"Content-Range": "bytes 1000-1499/1500"})

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=MagicMock(), resume_from=1000)

    assert result == local_path
    assert local_path.stat().st_size == 1500
    assert local_path.read_bytes() == b"A" * 1000 + b"B" * 500

    # Verify Range header was sent
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].headers["Range"] == "bytes=1000-"


def test_fetch_resume_fallback_no_range_support(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _fetch falls back to full download when server doesn't support Range"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create partial file
    local_path.write_bytes(b"A" * 1000)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    # Server returns 200 (ignores Range header)
    httpx_mock.add_response(status_code=200, content=b"X" * 1500)

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=MagicMock(), resume_from=1000)

    assert result == local_path
    # Should re-download full file
    assert local_path.read_bytes() == b"X" * 1500


def test_fetch_resume_416_range_not_satisfiable(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _fetch handles 416 Range Not Satisfiable (file already complete)"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # File already complete
    local_path.write_bytes(b"A" * 1500)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    httpx_mock.add_response(status_code=416)

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=MagicMock(), resume_from=1500)

    assert result == local_path
    # File should remain unchanged
    assert local_path.read_bytes() == b"A" * 1500


def test_download_asset_detects_partial_file(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _download_asset detects and resumes partial files"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create partial file (500 of 1000 bytes)
    local_path.write_bytes(b"A" * 500)

    # Mock HEAD request for file size check
    httpx_mock.add_response(method="GET", headers={"Content-Length": "1000"})

    # Mock resume request
    httpx_mock.add_response(status_code=206, content=b"B" * 500, headers={"Content-Range": "bytes 500-999/1000"})

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=True)

    assert result == local_path
    assert local_path.stat().st_size == 1000
    assert local_path.read_bytes() == b"A" * 500 + b"B" * 500


def test_download_asset_skips_complete_file(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _download_asset skips download when file is already complete"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create complete file
    local_path.write_bytes(b"COMPLETE" * 100)
    complete_size = local_path.stat().st_size

    # Mock HEAD request for file size check
    httpx_mock.add_response(method="GET", headers={"Content-Length": str(complete_size)})

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=True)

    assert result == local_path
    # File should be unchanged
    assert local_path.read_bytes() == b"COMPLETE" * 100
    # Should only make HEAD request, no download
    assert len(httpx_mock.get_requests()) == 1


def test_download_asset_corrupted_file_redownload(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _download_asset re-downloads when existing file is larger than expected"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create corrupted file (larger than expected)
    local_path.write_bytes(b"X" * 2000)

    # Mock HEAD request for file size check (expected size is 1000)
    httpx_mock.add_response(method="GET", headers={"Content-Length": "1000"})

    # Mock fresh download
    httpx_mock.add_response(status_code=200, content=b"GOOD" * 250)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=True)

    assert result == local_path
    assert local_path.stat().st_size == 1000
    assert local_path.read_bytes() == b"GOOD" * 250


def test_download_asset_resume_disabled(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _download_asset skips existing files when resume is disabled"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Partial file exists
    local_path.write_bytes(b"A" * 500)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=False)

    # Should skip download (file exists, resume disabled)
    assert result == local_path
    assert local_path.read_bytes() == b"A" * 500
    # No HTTP requests should be made
    assert len(httpx_mock.get_requests()) == 0


def test_download_asset_unknown_size_skips_resume(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that _download_asset skips existing files when asset size is unknown"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Partial file exists
    local_path.write_bytes(b"A" * 500)

    # Mock HEAD request fails (unknown size)
    httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=True)

    # Should skip download (unknown size, can't resume reliably)
    assert result == local_path
    assert local_path.read_bytes() == b"A" * 500


def test_fetch_resume_with_progress(httpx_mock: HTTPXMock, tmp_path: Path):
    """Test that progress tracking works correctly with resume"""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Create partial file (1000 bytes)
    local_path.write_bytes(b"A" * 1000)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    # Mock 206 response with remaining bytes
    httpx_mock.add_response(status_code=206, content=b"B" * 500, headers={"Content-Range": "bytes 1000-1499/1500"})

    mock_progress = MagicMock()
    result = _fetch(dl_request, asset_size=1500, show_progress=True, progress=mock_progress, resume_from=1000)

    assert result == local_path
    assert local_path.stat().st_size == 1500

    # Verify progress was updated with initial offset
    assert mock_progress.add_task.called
    assert mock_progress.update.called

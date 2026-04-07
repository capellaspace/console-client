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
    _get_filename,
    _safe_local_path,
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


@pytest.fixture
def resume_test_setup(tmp_path):
    """Shared setup for resume functionality tests."""

    def _setup(partial_bytes: bytes | None = None):
        """
        Create test objects for resume tests.

        Args:
            partial_bytes: Initial bytes to write to file (None for no file)

        Returns:
            Tuple of (test_url, local_path, dl_request, mock_progress)
        """
        test_url = "https://example.com/test-asset.tif"
        local_path = tmp_path / "test-asset.tif"

        if partial_bytes is not None:
            local_path.write_bytes(partial_bytes)

        dl_request = DownloadRequest(
            url=test_url,
            local_path=local_path,
            asset_key="HH",
            stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
        )

        mock_progress = MagicMock()

        return test_url, local_path, dl_request, mock_progress

    return _setup


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


def test_fetch_resume_partial_download(httpx_mock: HTTPXMock, resume_test_setup):
    """Test that _fetch successfully resumes a partial download using 206 Partial Content"""
    test_url, local_path, dl_request, mock_progress = resume_test_setup(partial_bytes=b"A" * 1000)

    # Mock 206 response with remaining bytes
    httpx_mock.add_response(status_code=206, content=b"B" * 500, headers={"Content-Range": "bytes 1000-1499/1500"})

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=mock_progress, resume_from=1000)

    assert result == local_path
    assert local_path.stat().st_size == 1500
    assert local_path.read_bytes() == b"A" * 1000 + b"B" * 500

    # Verify Range header was sent
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].headers["Range"] == "bytes=1000-"


def test_fetch_resume_fallback_no_range_support(httpx_mock: HTTPXMock, resume_test_setup):
    """Test that _fetch falls back to full download when server doesn't support Range"""
    test_url, local_path, dl_request, mock_progress = resume_test_setup(partial_bytes=b"A" * 1000)

    # Server returns 200 (ignores Range header)
    httpx_mock.add_response(status_code=200, content=b"X" * 1500)

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=mock_progress, resume_from=1000)

    assert result == local_path
    # Should re-download full file
    assert local_path.read_bytes() == b"X" * 1500


def test_fetch_resume_416_range_not_satisfiable(httpx_mock: HTTPXMock, resume_test_setup):
    """Test that _fetch handles 416 Range Not Satisfiable (file already complete)"""
    test_url, local_path, dl_request, mock_progress = resume_test_setup(partial_bytes=b"A" * 1500)

    httpx_mock.add_response(status_code=416)

    result = _fetch(dl_request, asset_size=1500, show_progress=False, progress=mock_progress, resume_from=1500)

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


def test_fetch_resume_with_progress(httpx_mock: HTTPXMock, resume_test_setup):
    """Test that progress tracking works correctly with resume"""
    test_url, local_path, dl_request, mock_progress = resume_test_setup(partial_bytes=b"A" * 1000)

    # Mock 206 response with remaining bytes
    httpx_mock.add_response(status_code=206, content=b"B" * 500, headers={"Content-Range": "bytes 1000-1499/1500"})

    result = _fetch(dl_request, asset_size=1500, show_progress=True, progress=mock_progress, resume_from=1000)

    assert result == local_path
    assert local_path.stat().st_size == 1500

    # Verify progress was updated with initial offset
    assert mock_progress.add_task.called
    assert mock_progress.update.called


PRESIGNED_BASE = "https://s3.amazonaws.com/bucket"


@pytest.mark.parametrize(
    "url, expected",
    [
        (f"{PRESIGNED_BASE}/image.tif?X-Amz-Signature=abc123", "image.tif"),
        (
            f"{PRESIGNED_BASE}/CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740.tif",
            "CAPELLA_C05_SM_GEO_HH_20210727091736_20210727091740.tif",
        ),
        (f"{PRESIGNED_BASE}/path/to/deep/file.json", "file.json"),
    ],
)
def test_get_filename_extracts_name(url, expected):
    assert _get_filename(url) == expected


def test_safe_local_path_normal(tmp_path):
    url = f"{PRESIGNED_BASE}/image.tif?X-Amz-Signature=abc123"
    result = _safe_local_path(tmp_path, url)
    assert result == tmp_path / "image.tif"


@pytest.mark.parametrize(
    "crafted_url",
    [
        f"{PRESIGNED_BASE}/%2F..%2F..%2Fetc%2Fpasswd",
        "https://evil.com/../../../../etc/passwd",
    ],
)
def test_safe_local_path_rejects_traversal(tmp_path, crafted_url):
    result = _safe_local_path(tmp_path, crafted_url)
    assert result.is_relative_to(tmp_path)


def test_safe_local_path_absolute_filename_rejected(tmp_path, monkeypatch):
    # Simulate a hypothetical case where _get_filename returns an absolute-
    # looking name by monkeypatching it; _safe_local_path must reject it.
    monkeypatch.setattr(
        "capella_console_client.assets._get_filename",
        lambda url: "../../../etc/passwd",
    )
    with pytest.raises(ValueError, match="Unsafe filename rejected"):
        _safe_local_path(tmp_path, "https://example.com/anything")


def test_download_asset_raises_on_size_mismatch(httpx_mock: HTTPXMock, tmp_path: Path):
    """Truncated download (bytes written < Content-Length) must raise ValueError."""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # Server advertises 1000 bytes but only delivers 800
    httpx_mock.add_response(method="GET", headers={"Content-Length": "1000"})
    httpx_mock.add_response(status_code=200, content=b"X" * 800)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    with pytest.raises(ValueError, match="Download size mismatch"):
        _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=False)


def test_fetch_connect_error_strips_query_string(tmp_path: Path, monkeypatch):
    """ConnectError message must not expose presigned URL query params (AWS tokens)."""
    presigned_url = "https://s3.amazonaws.com/bucket/image.tif?X-Amz-Signature=secret123&X-Amz-Credential=key"
    local_path = tmp_path / "image.tif"

    dl_request = DownloadRequest(
        url=presigned_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    import httpx as _httpx

    monkeypatch.setattr(_httpx, "stream", MagicMock(side_effect=_httpx.ConnectError("connection refused")))

    from capella_console_client.exceptions import ConnectError as CapellaConnectError

    with pytest.raises(CapellaConnectError) as exc_info:
        _fetch(dl_request, asset_size=1000, show_progress=False, progress=MagicMock())

    error_message = str(exc_info.value)
    assert "secret123" not in error_message
    assert "X-Amz-Signature" not in error_message
    assert "image.tif" in error_message  # path retained for debuggability


def test_download_asset_no_size_check_when_content_length_unknown(httpx_mock: HTTPXMock, tmp_path: Path):
    """When Content-Length is unavailable (asset_size=-1) no size check is performed."""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    # No Content-Length header → _get_asset_bytesize raises, asset_size=-1
    httpx_mock.add_response(method="GET", headers={})
    httpx_mock.add_response(status_code=200, content=b"X" * 500)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=False)
    assert result == local_path
    assert local_path.stat().st_size == 500


def test_download_asset_passes_when_sizes_match(httpx_mock: HTTPXMock, tmp_path: Path):
    """A complete download where bytes written == Content-Length must succeed."""
    test_url = "https://example.com/test-asset.tif"
    local_path = tmp_path / "test-asset.tif"

    httpx_mock.add_response(method="GET", headers={"Content-Length": "1000"})
    httpx_mock.add_response(status_code=200, content=b"X" * 1000)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=local_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    result = _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=False)
    assert result == local_path
    assert local_path.stat().st_size == 1000


def test_download_asset_size_check_applies_to_s3path(httpx_mock: HTTPXMock):
    """Size mismatch check also fires for S3Path targets (uses .stat().st_size)."""
    test_url = "https://example.com/test-asset.tif"

    # Mock an S3Path-like object: write succeeds but stat reports a shorter file
    mock_s3_path = MagicMock()
    mock_s3_path.exists.return_value = False
    mock_s3_path.is_dir.return_value = False
    mock_s3_path.stat.return_value.st_size = 800  # truncated
    mock_s3_path.name = "test-asset.tif"
    mock_s3_path.open.return_value.__enter__ = lambda s: s
    mock_s3_path.open.return_value.__exit__ = MagicMock(return_value=False)
    mock_s3_path.write = MagicMock()

    httpx_mock.add_response(method="GET", headers={"Content-Length": "1000"})
    httpx_mock.add_response(status_code=200, content=b"X" * 800)

    dl_request = DownloadRequest(
        url=test_url,
        local_path=mock_s3_path,
        asset_key="HH",
        stac_id="CAPELLA_TEST_SM_GEO_HH_20210727091736_20210727091740",
    )

    with pytest.raises(ValueError, match="Download size mismatch"):
        _download_asset(dl_request, override=False, show_progress=False, progress=MagicMock(), enable_resume=False)

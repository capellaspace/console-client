#!/usr/bin/env python

"""Tests for `capella_console_client` package."""

import tempfile
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.s3 import S3Path
from .test_data import (
    get_mock_responses,
    create_mock_asset_hrefs,
    create_mock_items_presigned,
    DUMMY_STAC_IDS,
)
from capella_console_client.exceptions import ConnectError

MOCK_ASSETS_PRESIGNED = create_mock_asset_hrefs()
MOCK_ASSET_HREF = MOCK_ASSETS_PRESIGNED["HH"]["href"]
MOCK_ITEM_PRESIGNED = create_mock_items_presigned()


def test_get_presigned_assets(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1/download",
        json=get_mock_responses("/orders/1/download"),
    )

    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    presigned_assets = client.get_presigned_assets(order_id="1")
    assert presigned_assets[0] == get_mock_responses("/orders/1/download")[0]["assets"]


def test_get_presigned_assets_filtered(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    presigned_assets = client.get_presigned_assets(order_id="2", stac_ids=[DUMMY_STAC_IDS[0]])
    assert len(presigned_assets) == 1

    mock_response = get_mock_responses("/orders/2/download")
    order_2_assets = [m["assets"] for m in mock_response if m["id"] == DUMMY_STAC_IDS[0]][0]
    assert presigned_assets[0] == order_2_assets


def test_get_presigned_assets_filtered_no_overlap(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    presigned_assets = client.get_presigned_assets(order_id="2", stac_ids=["3", "4"])
    assert presigned_assets == []


def test_asset_download(download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path)
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_asset_download_progress(big_download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    big_download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, show_progress=True)
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_verbose_asset_download(verbose_download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    verbose_download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path)
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_asset_download_defaults_to_temp(download_client):
    path = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF)
    assert path.exists()
    assert path.read_text() == "MOCK_CONTENT"
    path.unlink()


def test_asset_download_s3path(download_client, s3path_mock):
    path = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=s3path_mock)
    assert isinstance(S3Path(path), S3Path)
    assert path.exists()
    assert path.is_file()


def test_asset_download_s3path_string(download_client, s3path_mock, monkeypatch):
    monkeypatch.setattr("capella_console_client.client.S3Path", lambda x: s3path_mock)
    path = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path="s3://mock-bucket/mock-path")
    assert isinstance(S3Path(path), S3Path)
    assert path.exists()
    assert path.is_file()


def test_asset_download_does_not_override(test_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    local_path.write_text("ORIG_CONTENT")
    local_path = test_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path)
    assert local_path.read_text() == "ORIG_CONTENT"
    local_path.unlink()


def test_asset_download_does_override(download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    local_path.write_text("ORIG_CONTENT")
    local_path = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, override=True)
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_product_download_dir_exists(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir)
        paths = list(paths_by_key.values())

        assert all([p.exists() for p in paths])
        assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

        # within temp_dir
        for p in paths:
            assert p.relative_to(temp_dir)


def test_product_download_dir_exists_from_order(download_client, monkeypatch, disable_validate_uuid):
    monkeypatch.setattr(
        CapellaConsoleClient,
        "get_presigned_assets",
        lambda x, y: [i["assets"] for i in get_mock_responses("/orders/1/download")],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(order_id="1", local_dir=temp_dir)
        paths = list(paths_by_key.values())

        assert all([p.exists() for p in paths])
        assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

        # within temp_dir
        for p in paths:
            assert p.relative_to(temp_dir)


def test_product_download_threaded_within_dir(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, threaded=True)
        paths = list(paths_by_key.values())

        assert all([p.exists() for p in paths])
        assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

        # within temp_dir
        for p in paths:
            assert p.relative_to(temp_dir)


def test_download_product_missing_input(test_client):
    with pytest.raises(ValueError):
        test_client.download_product()


def test_download_products_missing_input(test_client):
    with pytest.raises(ValueError):
        test_client.download_products()


def test_products_download_threaded_within_dir(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        items_presigned = [MOCK_ITEM_PRESIGNED, MOCK_ITEM_PRESIGNED]

        paths_by_stac_id_and_key = download_client.download_products(items_presigned, local_dir=temp_dir, threaded=True)
        for stac_id in paths_by_stac_id_and_key:
            paths = list(paths_by_stac_id_and_key[stac_id].values())

            assert all([p.exists() for p in paths])
            assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

            # within temp_dir
            for p in paths:
                assert p.relative_to(temp_dir)


def test_download_products_s3path(download_client, s3path_mock):
    paths_by_stac_id_and_key = download_client.download_products([MOCK_ITEM_PRESIGNED], local_dir=s3path_mock)

    assert paths_by_stac_id_and_key
    s3path_mock.__truediv__.assert_called()

    for stac_id, assets_dict in paths_by_stac_id_and_key.items():
        assert stac_id in DUMMY_STAC_IDS
        for _, path in assets_dict.items():
            assert isinstance(S3Path(path), S3Path)
            assert path.exists()
            assert path.relative_to(s3path_mock)
            assert path.is_file()


def test_product_download_asset_include(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, include=["HH"])
        paths = list(paths_by_key.values())
        assert len(paths) == 1
        assert "thumb.png" not in str(paths[0])


def test_product_download_asset_include_str(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, include="HH")
        paths = list(paths_by_key.values())
        assert len(paths) == 1
        asset_keys = list(paths_by_key.keys())
        assert "HH" in asset_keys
        assert "thumbnail" not in asset_keys


def test_product_download_exclude(test_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = test_client.download_product(
            MOCK_ASSETS_PRESIGNED,
            local_dir=temp_dir,
            exclude=["HH", "thumbnail"],
            threaded=False,
        )
        assert "HH" not in paths_by_key
        assert "thumbnail" not in paths_by_key


def test_product_download_exclude_str(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, exclude="HH")
        assert "HH" not in paths_by_key


def test_product_download_exclude_raster(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, exclude="raster")
        assert "HH" not in paths_by_key


def test_product_download_exclude_overrides_include(test_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        paths_by_key = test_client.download_product(
            MOCK_ASSETS_PRESIGNED,
            local_dir=temp_dir,
            include=["HH"],
            exclude=["HH", "thumbnail"],
        )
        assert len(paths_by_key) == 0


def _shared_dl_asserts(paths_by_stac_id_and_key, temp_dir):
    for stac_id in paths_by_stac_id_and_key:
        paths = list(paths_by_stac_id_and_key[stac_id].values())

        assert all([p.exists() for p in paths])
        assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

        # within temp_dir
        for p in paths:
            assert p.relative_to(temp_dir)

        assert len(paths) == 1
        assert "thumb.png" not in str(paths[0])


def test_download_products_for_tasking_request(
    verbose_download_multiple_client,
    auth_httpx_mock,
    disable_validate_uuid,
    assert_all_responses_were_requested,
):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/abc",
        json=get_mock_responses("/task/abc"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/collects/list/abc",
        json=get_mock_responses("/collects/list/abc"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        paths_by_stac_id_and_key = verbose_download_multiple_client.download_products(
            tasking_request_id="abc", local_dir=temp_dir, include=["HH"]
        )

        _shared_dl_asserts(paths_by_stac_id_and_key, temp_dir)


def test_download_products_for_order_id(verbose_download_multiple_client, disable_validate_uuid):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        paths_by_stac_id_and_key = verbose_download_multiple_client.download_products(
            order_id="1", local_dir=temp_dir, include=["HH"]
        )

        _shared_dl_asserts(paths_by_stac_id_and_key, temp_dir)


def test_download_products_for_collect_id(verbose_download_multiple_client, auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        paths_by_stac_id_and_key = verbose_download_multiple_client.download_products(
            collect_id="abc", local_dir=temp_dir, include=["HH"]
        )
        _shared_dl_asserts(paths_by_stac_id_and_key, temp_dir)


def test_download_products_with_product_types_filter(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        items_presigned = [MOCK_ITEM_PRESIGNED, MOCK_ITEM_PRESIGNED]

        paths_by_stac_id_and_key = download_client.download_products(
            items_presigned, local_dir=temp_dir, product_types=["GEO"]
        )
        for stac_id in paths_by_stac_id_and_key:
            paths = list(paths_by_stac_id_and_key[stac_id].values())

            assert all([p.exists() for p in paths])
            assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

            # within temp_dir
            for p in paths:
                assert p.relative_to(temp_dir)


def test_download_products_with_product_types_filter_all_exclude(download_client):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        items_presigned = [MOCK_ITEM_PRESIGNED, MOCK_ITEM_PRESIGNED]

        paths_by_stac_id_and_key = download_client.download_products(
            items_presigned, local_dir=temp_dir, product_types=["SIDD"]
        )
        assert paths_by_stac_id_and_key == {}


def test_get_asset_bytesize(download_client, auth_httpx_mock):
    auth_httpx_mock.add_response(text="MOCK_CONTENT", headers={"Content-Length": "127"})

    bytesize = download_client.get_asset_bytesize(MOCK_ASSET_HREF)
    assert bytesize == 127


def test_get_asset_bytesize_raises(test_client, auth_httpx_mock: HTTPXMock):
    def raise_conntection_error(request):
        raise httpx.ConnectError("NO CONNECTION")

    auth_httpx_mock.add_callback(raise_conntection_error)

    with pytest.raises(ConnectError):
        test_client.get_asset_bytesize(MOCK_ASSET_HREF)


# Resume functionality integration tests


def test_download_asset_resume_partial_file(download_client, auth_httpx_mock: HTTPXMock):
    """Test that client.download_asset() successfully resumes a partial download"""
    local_path = Path(tempfile.NamedTemporaryFile(delete=False).name)

    # Create partial file (6 of 12 bytes)
    local_path.write_text("MOCK_C")

    # Mock all requests to the asset URL with a single callback
    def asset_callback(request):
        if "Range" in request.headers and request.headers["Range"] == "bytes=6-":
            return httpx.Response(status_code=206, text="ONTENT", headers={"Content-Range": "bytes 6-11/12"})
        else:
            return httpx.Response(status_code=200, text="MOCK_CONTENT", headers={"Content-Length": "12"})

    auth_httpx_mock.add_callback(asset_callback, url=MOCK_ASSET_HREF)

    result = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, enable_resume=True)

    assert result == local_path
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"

    # Verify Range header was sent
    asset_requests = [r for r in auth_httpx_mock.get_requests() if MOCK_ASSET_HREF in str(r.url)]
    assert len(asset_requests) == 2
    assert asset_requests[1].headers["Range"] == "bytes=6-"

    local_path.unlink()


def test_download_asset_resume_disabled_skips_existing(download_client):
    """Test that download_asset with enable_resume=False skips existing files"""
    local_path = Path(tempfile.NamedTemporaryFile(delete=False).name)
    local_path.write_text("PARTIAL")

    result = download_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, enable_resume=False, override=False
    )

    assert result == local_path
    assert local_path.read_text() == "PARTIAL"  # Unchanged

    local_path.unlink()


def test_download_asset_complete_file_skipped(download_client, auth_httpx_mock: HTTPXMock):
    """Test that download_asset recognizes complete files and doesn't re-download"""
    local_path = Path(tempfile.NamedTemporaryFile(delete=False).name)
    # Use bytes to ensure exact size
    local_path.write_bytes(b"MOCK_CONTENT")

    # Verify file size is exactly 12 bytes
    assert local_path.stat().st_size == 12

    # Mock all requests
    def asset_callback(request):
        return httpx.Response(status_code=200, content=b"MOCK_CONTENT", headers={"Content-Length": "12"})

    auth_httpx_mock.add_callback(asset_callback, url=MOCK_ASSET_HREF)

    result = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, enable_resume=True)

    assert result == local_path
    # File should remain unchanged
    assert local_path.read_bytes() == b"MOCK_CONTENT"

    local_path.unlink()


def test_download_products_resume_partial_files(download_client, auth_httpx_mock: HTTPXMock):
    """Test that download_products resumes partial files for multiple assets"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Create directory structure for STAC ID
        stac_dir = temp_dir / DUMMY_STAC_IDS[0]
        stac_dir.mkdir(parents=True, exist_ok=True)

        # Create partial file for HH asset
        hh_file = stac_dir / "CAPELLA_C02_SM_GEO_HH_20210119154519_20210119154523.tif"
        hh_file.write_text("MOCK_C")

        # Use callback to handle different requests properly
        def asset_callback(request):
            # HH asset
            if "CAPELLA_C02_SM_GEO_HH" in str(request.url) and ".tif" in str(request.url):
                if "Range" in request.headers and request.headers["Range"] == "bytes=6-":
                    return httpx.Response(status_code=206, text="ONTENT", headers={"Content-Range": "bytes 6-11/12"})
                else:
                    return httpx.Response(status_code=200, text="MOCK_CONTENT", headers={"Content-Length": "12"})
            # Thumbnail asset
            elif ".png" in str(request.url):
                if "Range" in request.headers:
                    # Shouldn't resume thumbnail (doesn't exist yet)
                    return httpx.Response(status_code=200, text="MOCK_CONTENT", headers={"Content-Length": "12"})
                else:
                    return httpx.Response(status_code=200, text="MOCK_CONTENT", headers={"Content-Length": "12"})

        auth_httpx_mock.add_callback(asset_callback)

        paths_by_stac_id_and_key = download_client.download_products(
            [MOCK_ITEM_PRESIGNED], local_dir=temp_dir, enable_resume=True
        )

        # Verify both files are complete
        for stac_id, assets_dict in paths_by_stac_id_and_key.items():
            for asset_key, path in assets_dict.items():
                assert path.exists()
                assert path.read_text() == "MOCK_CONTENT"


def test_download_asset_fallback_when_range_unsupported(download_client, auth_httpx_mock: HTTPXMock):
    """Test that download falls back to full download when server doesn't support Range"""
    local_path = Path(tempfile.NamedTemporaryFile(delete=False).name)
    local_path.write_text("PARTIAL")

    # Mock file size check
    auth_httpx_mock.add_response(text="MOCK_CONTENT", headers={"Content-Length": "12"})

    # Server returns 200 instead of 206 (doesn't support Range)
    auth_httpx_mock.add_response(status_code=200, text="MOCK_CONTENT")

    result = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, enable_resume=True)

    assert result == local_path
    assert local_path.read_text() == "MOCK_CONTENT"

    local_path.unlink()

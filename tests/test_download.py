#!/usr/bin/env python

"""Tests for `capella_console_client` package."""

import tempfile
from pathlib import Path

import pytest

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from .test_data import (
    post_mock_responses,
    get_mock_responses,
    MOCK_ASSET_HREF,
    MOCK_ASSETS_PRESIGNED,
    search_catalog_get_stac_ids,
)


def test_get_presigned_assets(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1/download",
        json=get_mock_responses("/orders/1/download"),
    )

    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="1")
    assert presigned_assets[0] == get_mock_responses("/orders/1/download")[0]["assets"]


def test_get_presigned_assets_filtered(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="2", stac_ids=["2"])
    assert len(presigned_assets) == 1

    mock_response = get_mock_responses("/orders/2/download")
    order_2_assets = [m["assets"] for m in mock_response if m["id"] == "2"][0]
    assert presigned_assets[0] == order_2_assets


def test_get_presigned_assets_filtered_no_overlap(
    auth_httpx_mock, disable_validate_uuid
):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="2", stac_ids=["3", "4"])
    assert presigned_assets == []


def test_asset_download(download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    download_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path
    )
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_asset_download_progress(big_download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    big_download_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, show_progress=True
    )
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_verbose_asset_download(verbose_download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    assert not local_path.exists()
    verbose_download_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path
    )
    assert local_path.exists()
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_asset_download_defaults_to_temp(download_client):
    path = download_client.download_asset(pre_signed_url=MOCK_ASSET_HREF)
    assert path.exists()
    assert path.read_text() == "MOCK_CONTENT"
    path.unlink()


def test_asset_download_does_not_override(test_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    local_path.write_text("ORIG_CONTENT")
    local_path = test_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path
    )
    assert local_path.read_text() == "ORIG_CONTENT"
    local_path.unlink()


def test_asset_download_does_override(download_client):
    local_path = Path(tempfile.NamedTemporaryFile().name)
    local_path.write_text("ORIG_CONTENT")
    local_path = download_client.download_asset(
        pre_signed_url=MOCK_ASSET_HREF, local_path=local_path, override=True
    )
    assert local_path.read_text() == "MOCK_CONTENT"
    local_path.unlink()


def test_product_download_dir_exists(download_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir
        )
        paths = list(paths_by_key.values())

        assert all([p.exists() for p in paths])
        assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

        # within temp_dir
        for p in paths:
            assert p.relative_to(temp_dir)


def test_product_download_dir_exists_from_order(
    download_client, monkeypatch, disable_validate_uuid
):
    monkeypatch.setattr(
        CapellaConsoleClient,
        "get_presigned_assets",
        lambda x, y: [i["assets"] for i in get_mock_responses("/orders/1/download")],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            order_id="1", local_dir=temp_dir
        )
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
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, threaded=True
        )
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
        assets_presigned = [MOCK_ASSETS_PRESIGNED, MOCK_ASSETS_PRESIGNED]

        paths_by_stac_id_and_key = download_client.download_products(
            assets_presigned, local_dir=temp_dir, threaded=True
        )
        for stac_id in paths_by_stac_id_and_key:
            paths = list(paths_by_stac_id_and_key[stac_id].values())

            assert all([p.exists() for p in paths])
            assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

            # within temp_dir
            for p in paths:
                assert p.relative_to(temp_dir)


def test_product_download_asset_include(download_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, include=["HH"]
        )
        paths = list(paths_by_key.values())
        assert len(paths) == 1
        assert "thumb.png" not in str(paths[0])


def test_product_download_asset_include_str(download_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, include="HH"
        )
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
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, exclude=["HH", "thumbnail"]
        )
        assert "HH" not in paths_by_key
        assert "thumbnail" not in paths_by_key


def test_product_download_exclude_str(download_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, exclude="HH"
        )
        assert "HH" not in paths_by_key


def test_product_download_exclude_raster(download_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = download_client.download_product(
            MOCK_ASSETS_PRESIGNED, local_dir=temp_dir, exclude="raster"
        )
        assert "HH" not in paths_by_key


def test_product_download_exclude_overrides_include(test_client):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()
        paths_by_key = test_client.download_product(
            MOCK_ASSETS_PRESIGNED,
            local_dir=temp_dir,
            include=["HH"],
            exclude=["HH", "thumbnail"],
        )
        assert len(paths_by_key) == 0


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

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()

        paths_by_stac_id_and_key = verbose_download_multiple_client.download_products(
            tasking_request_id="abc", local_dir=temp_dir, include=["HH"]
        )

        for stac_id in paths_by_stac_id_and_key:
            paths = list(paths_by_stac_id_and_key[stac_id].values())

            assert all([p.exists() for p in paths])
            assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

            # within temp_dir
            for p in paths:
                assert p.relative_to(temp_dir)

            assert len(paths) == 1
            assert "thumb.png" not in str(paths[0])


def test_download_products_for_collect_id(
    verbose_download_multiple_client, auth_httpx_mock, disable_validate_uuid
):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()

        paths_by_stac_id_and_key = verbose_download_multiple_client.download_products(
            collect_id="abc", local_dir=temp_dir, include=["HH"]
        )

        for stac_id in paths_by_stac_id_and_key:
            paths = list(paths_by_stac_id_and_key[stac_id].values())

            assert all([p.exists() for p in paths])
            assert all([p.read_text() == "MOCK_CONTENT" for p in paths])

            # within temp_dir
            for p in paths:
                assert p.relative_to(temp_dir)

            assert len(paths) == 1
            assert "thumb.png" not in str(paths[0])

#!/usr/bin/env python

"""Tests for `capella_console_client` package."""

import tempfile
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
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

    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="1")
    assert presigned_assets[0] == get_mock_responses("/orders/1/download")[0]["assets"]


def test_get_presigned_assets_filtered(auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
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
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
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

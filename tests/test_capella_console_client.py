#!/usr/bin/env python

"""Tests for `capella_console_client` package."""

from unittest.mock import MagicMock
import base64
from datetime import datetime, timedelta
from copy import deepcopy
import tempfile
import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

import capella_console_client.session as c_session

from capella_console_client.config import CONSOLE_API_URL, DEFAULT_TIMEOUT
from capella_console_client import CapellaConsoleClient
from capella_console_client import client as capella_client_module
from capella_console_client.exceptions import (
    NoValidStacIdsError,
    OrderRejectedError,
    TaskNotCompleteError,
    AuthenticationError,
)
from .test_data import (
    post_mock_responses,
    get_mock_responses,
    get_search_test_cases,
    MOCK_ASSET_HREF,
    MOCK_ASSETS_PRESIGNED,
    search_catalog_get_stac_ids,
)
from capella_console_client import client


@pytest.fixture
def auth_httpx_mock(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/token", json=post_mock_responses("/token")
    )

    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user")
    )
    yield httpx_mock


@pytest.fixture
def test_client(auth_httpx_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    yield client


@pytest.fixture
def verbose_test_client(auth_httpx_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW", verbose=True)
    yield client


@pytest.fixture
def search_client(test_client, monkeypatch):
    monkeypatch.setattr(client, "_paginated_search", MagicMock())
    yield test_client


@pytest.fixture
def order_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )
    yield test_client


@pytest.fixture
def non_expired_order_mock(test_client, auth_httpx_mock):
    orders = get_mock_responses("/orders")
    non_expired_order = deepcopy(orders[0])
    non_expired_order["expirationDate"] = (
        datetime.utcnow() + timedelta(minutes=10)
    ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    orders.append(non_expired_order)
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID", json=orders
    )

    yield test_client, non_expired_order


def test_basic_auth(auth_httpx_mock: HTTPXMock):
    email = "MOCK_EMAIL"
    pw = "MOCK_PW"

    client = CapellaConsoleClient(email=email, password=pw)
    _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw)


def test_failed_basic_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/token",
        status_code=400,
        json={
            "error": {
                "message": "Incorrect username or password.",
                "code": "GENERAL_API_ERROR",
            }
        },
    )
    with pytest.raises(AuthenticationError):
        CapellaConsoleClient(email="MOCK_INVALID_EMAIL", password="MOCK_INVALID_PW")


def test_basic_auth_takes_precedence(auth_httpx_mock: HTTPXMock):
    email = "MOCK_EMAIL"
    pw = "MOCK_PW"
    token = "MOCK_TOKEN"

    client = CapellaConsoleClient(email=email, password=pw, token=token)
    _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw)


def _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw):
    requests = auth_httpx_mock.get_requests()
    assert requests[0].url == f"{CONSOLE_API_URL}/token"
    assert requests[0].method == "POST"

    basic_token = base64.b64encode(f"{email}:{pw}".encode()).decode("utf-8")
    assert requests[0].headers["authorization"] == f"Basic {basic_token}"
    assert requests[1].url == f"{CONSOLE_API_URL}/user"
    assert requests[1].method == "GET"

    assert "Authorization" in client._sesh.headers
    mock_access_token = post_mock_responses("/token")["accessToken"]
    assert client._sesh.headers["Authorization"] == f"Bearer {mock_access_token}"


def test_token_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user")
    )

    token = "MOCK_TOKEN"

    client = CapellaConsoleClient(token=token)
    requests = httpx_mock.get_requests()

    assert requests[0].url == f"{CONSOLE_API_URL}/user"
    assert requests[0].method == "GET"

    assert "Authorization" in client._sesh.headers
    mock_access_token = post_mock_responses("/token")["accessToken"]
    assert client._sesh.headers["Authorization"] == f"Bearer {mock_access_token}"


def test_token_auth_no_check(httpx_mock: HTTPXMock):
    token = "MOCK_TOKEN"
    client = CapellaConsoleClient(token=token, no_token_check=True)
    requests = httpx_mock.get_requests()

    assert "Authorization" in client._sesh.headers
    assert client._sesh.headers["Authorization"] == f"Bearer {token}"
    assert len(requests) == 0


@pytest.mark.parametrize(
    "email,pw,token",
    [
        (None, None, None),
        ("", "", ""),
        (None, "MOCK_PW", None),
        ("MOCK_EMAIL", None, None),
    ],
)
def test_authenticate_missing_data(email, pw, token):
    with pytest.raises(ValueError):
        CapellaConsoleClient(email=email, password=pw, token=token)


def test_whoami(auth_httpx_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    whoami = client.whoami()

    assert whoami == get_mock_responses("/user")


def test_chatty_client(auth_httpx_mock):
    # chatty client
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW", verbose=True)


@pytest.fixture
def authed_tasking_request_mock(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/abc",
        json=get_mock_responses("/task/abc"),
    )
    yield auth_httpx_mock


def test_get_task(test_client, authed_tasking_request_mock):
    task = test_client.get_task("abc")

    assert task == get_mock_responses("/task/abc")
    assert task["properties"]["taskingrequestId"] == "abc"


def test_task_is_completed(authed_tasking_request_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    task = client.get_task("abc")

    assert client.is_task_completed(task) == True


def test_get_collects_for_task(test_client, authed_tasking_request_mock):
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}/collects/list/abc",
        json=get_mock_responses("/collects/list/abc"),
    )

    task = test_client.get_task("abc")
    collects = test_client.get_collects_for_task(task)

    assert collects == get_mock_responses("/collects/list/abc")


def test_get_collects_for_task_not_completed(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/def",
        json=get_mock_responses("/task/def"),
    )

    # we should get task 'def', see that it's not completed, and throw an exception
    task = test_client.get_task("def")

    with pytest.raises(TaskNotCompleteError):
        test_client.get_collects_for_task(task)


@pytest.mark.parametrize("search_args,expected", get_search_test_cases())
def test_search(search_args, expected, search_client):
    search_client.search(**search_args)
    assert client._paginated_search.call_args[0][1] == expected


def test_list_specific_order(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1", json=get_mock_responses("/orders")[0]
    )
    order = test_client.list_orders(order_ids=["1"])
    assert order == get_mock_responses("/orders")


def test_list_all_orders(order_client):
    orders = order_client.list_orders()
    assert orders == get_mock_responses("/orders")


def test_list_no_active_orders(order_client):
    orders = order_client.list_orders(is_active=True)
    assert orders == []


def test_list_active_orders_with_order_ids(test_client, monkeypatch):
    monkeypatch.setattr(
        capella_client_module,
        "_get_non_expired_orders",
        lambda session: get_mock_responses("/orders"),
    )
    orders = test_client.list_orders(is_active=True, order_ids=["1"])
    assert orders == get_mock_responses("/orders")


def test_list_active_orders(non_expired_order_mock):
    client, non_expired_order = non_expired_order_mock
    active_orders = client.list_orders(is_active=True)
    assert active_orders == [non_expired_order]


def test_submit_order_not_previously_ordered_check_active_orders(
    order_client, httpx_mock
):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={"features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}]},
    )
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=post_mock_responses("/submitOrder"),
    )
    order_id = order_client.submit_order(
        stac_ids=["MOCK_STAC_ID"], check_active_orders=True
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(
        method="POST", url=f"{CONSOLE_API_URL}/orders"
    )
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_not_previously_ordered_no_check_active_orders(
    test_client, httpx_mock
):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={"features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}]},
    )
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=post_mock_responses("/submitOrder"),
    )
    order_id = test_client.submit_order(
        stac_ids=["MOCK_STAC_ID"], check_active_orders=False
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(
        method="POST", url=f"{CONSOLE_API_URL}/orders"
    )
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_previously_ordered(non_expired_order_mock, httpx_mock):
    client, non_expired_order = non_expired_order_mock

    order_id = client.submit_order(
        stac_ids=["CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225"],
        check_active_orders=True,
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    assert (
        httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders") is None
    )


def test_submit_order_invalid_stac_id(test_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        method="POST",
        json={"features": []},
    )

    with pytest.raises(NoValidStacIdsError):
        test_client.submit_order(stac_ids=["DOES_NOT_EXISTS"])


def test_submit_order_rejected(test_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=get_mock_responses("/orders_rejected"),
    )
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        method="POST",
        json={
            "features": [
                {
                    "id": "CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225",
                    "collection": "capella-test",
                }
            ]
        },
    )

    with pytest.raises(OrderRejectedError):
        test_client.submit_order(stac_ids=["DOES_NOT_EXISTS"])


def test_submit_order_items(test_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={"features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}]},
    )

    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=post_mock_responses("/submitOrder"),
    )
    order_id = test_client.submit_order(
        items=[{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
        check_active_orders=False,
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(
        method="POST", url=f"{CONSOLE_API_URL}/orders"
    )
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_get_presigned_assets(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1/download",
        json=get_mock_responses("/orders/1/download"),
    )

    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="1")
    assert presigned_assets[0] == get_mock_responses("/orders/1/download")[0]["assets"]


def test_get_presigned_assets_filtered(auth_httpx_mock):
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


def test_get_presigned_assets_filtered_no_overlap(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/2/download",
        json=get_mock_responses("/orders/2/download"),
    )
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    presigned_assets = client.get_presigned_assets(order_id="2", stac_ids=["3", "4"])
    assert presigned_assets == []


@pytest.fixture
def download_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(data="MOCK_CONTENT", headers={"Content-Length": "127"})
    yield test_client


@pytest.fixture
def big_download_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        data="MOCK_CONTENT", headers={"Content-Length": "12700"}
    )
    yield test_client


@pytest.fixture
def verbose_download_client(verbose_test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(data="MOCK_CONTENT", headers={"Content-Length": "127"})
    yield verbose_test_client


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


def test_download_products_for_task(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/abc",
        json=get_mock_responses("/task/abc"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/collects/list/abc",
        json=get_mock_responses("/collects/list/abc"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json=search_catalog_get_stac_ids(),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        json=post_mock_responses("/submitOrder"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1/download",
        json=get_mock_responses("/orders/1/download"),
    )
    auth_httpx_mock.add_response(
        url=MOCK_ASSET_HREF, data="MOCK_CONTENT", headers={"Content-Length": "127"}
    )

    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        assert temp_dir.exists()

        paths_by_stac_id_and_key = client.download_products_for_task(
            "abc", local_dir=temp_dir, include=["HH"]
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

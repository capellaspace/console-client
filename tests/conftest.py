from unittest.mock import MagicMock
from copy import deepcopy
from datetime import datetime, timedelta

import pytest
from pytest_httpx import HTTPXMock

from capella_console_client import client as capella_client_module
from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client import client

from .test_data import (
    post_mock_responses,
    get_mock_responses,
)


@pytest.fixture
def disable_validate_uuid(monkeypatch):
    monkeypatch.setattr(capella_client_module, "_validate_uuid", lambda x: None)


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


@pytest.fixture
def authed_tasking_request_mock(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/abc",
        json=get_mock_responses("/task/abc"),
    )
    yield auth_httpx_mock


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

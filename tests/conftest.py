from unittest.mock import MagicMock
from copy import deepcopy
from datetime import datetime, timedelta
import re

import httpx
import pytest
from pytest_httpx import HTTPXMock

from capella_console_client import client as capella_client_module
from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client import client
from capella_console_client import tasking_request as tasking_modules
from capella_console_client.s3 import S3Path

from .test_data import (
    post_mock_responses,
    get_mock_responses,
    get_canned_search_results_single_page,
    get_canned_search_results_multi_page_page1,
    get_canned_search_results_multi_page_page2,
    create_mock_asset_hrefs,
)


MOCK_ASSET_HREF = create_mock_asset_hrefs()["HH"]["href"]


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return False


@pytest.fixture
def disable_validate_uuid(monkeypatch):
    monkeypatch.setattr(capella_client_module, "_validate_uuid", lambda x: None)
    monkeypatch.setattr(capella_client_module, "_validate_uuids", lambda x: None)
    monkeypatch.setattr(tasking_modules, "_validate_uuid", lambda x: None)


@pytest.fixture
def auth_httpx_mock(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{CONSOLE_API_URL}/token", json=post_mock_responses("/token"))

    httpx_mock.add_response(url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user"))
    yield httpx_mock


@pytest.fixture
def test_client(auth_httpx_mock):
    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    yield client


@pytest.fixture
def verbose_test_client(auth_httpx_mock):
    client = CapellaConsoleClient(api_key="MOCK_API_KEY", verbose=True)
    yield client


@pytest.fixture
def search_client(test_client, monkeypatch):
    monkeypatch.setattr(client.StacSearch, "fetch_all", MagicMock())
    yield test_client


@pytest.fixture
def review_client_insufficient_funds(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/review",
        json=get_mock_responses("/orders/review_insufficient_funds"),
    )
    yield test_client


@pytest.fixture
def order_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=post_mock_responses("/submitOrder"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/review",
        json=get_mock_responses("/orders/review_success"),
    )

    yield test_client


@pytest.fixture
def order_client_unsuccessful(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID",
        json=get_mock_responses("/orders"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/review",
        json=get_mock_responses("/orders/review_success"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        method="POST",
        json=post_mock_responses("/orders_rejected"),
    )
    yield test_client


@pytest.fixture
def non_expired_order_mock(test_client, auth_httpx_mock):
    orders = get_mock_responses("/orders")
    non_expired_order = deepcopy(orders[0])
    non_expired_order["expirationDate"] = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    orders.append(non_expired_order)
    auth_httpx_mock.add_response(url=f"{CONSOLE_API_URL}/orders?customerId=MOCK_ID", json=orders)

    yield test_client, non_expired_order


@pytest.fixture
def authed_tasking_request_mock(auth_httpx_mock):
    MOCK_IDENTIFIER_LIST = (
        "/task/abc",
        "/task/def",
        "/tasks/paged?page=1&limit=100&customerId=MOCK_ID",
        "/tasks/paged?page=1&limit=100&organizationId=MOCK_ORG_ID",
    )
    for mock_id in MOCK_IDENTIFIER_LIST:
        auth_httpx_mock.add_response(
            url=f"{CONSOLE_API_URL}{mock_id}",
            json=get_mock_responses(mock_id),
        )

    auth_httpx_mock.add_response(url=f"{CONSOLE_API_URL}/task", method="POST", json=post_mock_responses("/task"))
    yield auth_httpx_mock


@pytest.fixture
def authed_repeat_request_mock(auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/repeat-requests",
        method="POST",
        json=post_mock_responses("/repeat-requests"),
    )

    yield auth_httpx_mock


@pytest.fixture
def download_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(text="MOCK_CONTENT", headers={"Content-Length": "127"})
    yield test_client


@pytest.fixture
def big_download_client(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(text="MOCK_CONTENT", headers={"Content-Length": "12700"})
    yield test_client


@pytest.fixture
def verbose_download_client(verbose_test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(text="MOCK_CONTENT", headers={"Content-Length": "127"})
    yield verbose_test_client


@pytest.fixture
def verbose_download_multiple_client(verbose_test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json=get_canned_search_results_single_page(),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/review",
        json=get_mock_responses("/orders/review_success"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders",
        json=post_mock_responses("/submitOrder"),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/1/download",
        json=get_mock_responses("/orders/1/download"),
    )
    auth_httpx_mock.add_response(url=MOCK_ASSET_HREF, text="MOCK_CONTENT", headers={"Content-Length": "127"})
    yield verbose_test_client


@pytest.fixture
def single_page_search_client(verbose_test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json=get_canned_search_results_single_page(),
    )
    yield verbose_test_client


@pytest.fixture
def multi_page_search_client(verbose_test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json=get_canned_search_results_multi_page_page1(),
    )
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search?page=2",
        json=get_canned_search_results_multi_page_page2(),
    )
    yield verbose_test_client


@pytest.fixture
def s3path_mock():
    mock_s3path = MagicMock(spec=S3Path)
    mock_s3path.__truediv__.return_value = mock_s3path
    mock_s3path.__str__ = MagicMock(return_value="s3://mock-bucket/mock-path")
    yield mock_s3path


def patch_task_status_matcher(request: httpx.Request) -> bool:
    return request.method.upper() == "PATCH" and re.match(r"/task/[0-9a-f-]{36}/status$", str(request.url.path))


@pytest.fixture
def task_cancel_success_mock(authed_tasking_request_mock):
    authed_tasking_request_mock.add_response(
        url=re.compile(".*/task/[0-9a-f-]{36}/status$"), method="PATCH", json={"status": "canceled"}
    )
    yield authed_tasking_request_mock


CANCEL_ERR = {
    "message": "This transaction has been finalized with a status of 'customer-cancelled'. It cannot be further modified.",
    "code": "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION",
}


@pytest.fixture
def task_cancel_error_mock(authed_tasking_request_mock):
    authed_tasking_request_mock.add_response(
        url=re.compile(".*/task/[0-9a-f-]{36}/status$"),
        method="PATCH",
        status_code=400,
        json={"error": CANCEL_ERR},
    )
    yield authed_tasking_request_mock


@pytest.fixture
def task_cancel_partial_success_mock(authed_tasking_request_mock):
    authed_tasking_request_mock.add_response(
        url=re.compile(".*/task/[a-]{36}/status$"), method="PATCH", status_code=200, json={"status": "canceled"}
    )

    authed_tasking_request_mock.add_response(
        url=re.compile(".*/task/[b-]{36}/status$"),
        method="PATCH",
        status_code=400,
        json={"error": CANCEL_ERR},
    )

    yield authed_tasking_request_mock
